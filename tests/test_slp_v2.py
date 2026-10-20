"""Offline integration and state-preservation tests for SLP's adapter boundary."""

import copy
import json
import contextlib
import io
import os
from pathlib import Path
import shutil
import runpy
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/lib"))
from slp_core.common import Installation, SlpError, atomic_write, dump_toml
from slp_core.adapters import get_adapter
from slp_core import paseo


class SlpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="slp-v2-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").symlink_to(ROOT / "scripts", target_is_directory=True)
        shutil.copytree(ROOT / "config", self.root / "config", symlinks=True)
        provider_path = self.root / "config/providers/codex.toml"
        fixture_provider = tomllib.loads(provider_path.read_text())
        fixture_provider["account_routing"] = "isolated"
        provider_path.write_text(dump_toml(fixture_provider))
        self.canonical = self.root / "canonical"
        self.canonical.mkdir()
        (self.canonical / "config.toml").write_text('model = "gpt-6.1-sol"\n[tui]\n')
        (self.canonical / "auth.json").write_text("{}")
        self.catalog = self.root / "catalog.json"
        models = []
        for slug, visibility, efforts in [
            ("gpt-6.1-sol", "list", ["high", "xhigh", "ultra"]),
            ("other-model", "list", ["low", "high"]),
            ("hidden-internal", "hide", ["high"]),
        ]:
            models.append({"slug": slug, "display_name": slug, "visibility": visibility,
                           "multi_agent_version": "v2", "default_reasoning_level": "high",
                           "supported_reasoning_levels": [{"effort": e} for e in efforts]})
        self.catalog.write_text(json.dumps({"models": models}))
        self.fake = self.root / "fake-agent"
        self.fake.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                             'print(json.dumps({"args":sys.argv[1:],"home":os.environ.get("CODEX_HOME")}))\n')
        self.fake.chmod(0o755)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("SLP_") and key not in ("CODEX_HOME", "CODEX_BIN")}
        self.env.update(SLP_ROOT=str(self.root), SLP_MODEL_CATALOG=str(self.catalog),
                        SLP_RUNTIME_ROOT=str(self.root / ".runtime"),
                        XDG_STATE_HOME=str(self.root / "xdg-state"),
                        SLP_CANONICAL_HOME=str(self.canonical), CODEX_BIN=str(self.fake))
        self.environment = patch.dict(os.environ, self.env, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.installation = Installation.load()
        self.provider = self.installation.provider()
        self.adapter = get_adapter(self.provider)

    def run_cli(self, *args):
        return subprocess.run([str(ROOT / "scripts/slp"), *args], env=os.environ,
                              text=True, capture_output=True, timeout=10)

    def test_default_state_is_outside_checkout_and_honors_xdg(self):
        os.environ.pop("SLP_RUNTIME_ROOT")
        installation = Installation.load()
        self.assertEqual(installation.runtime, self.root / "xdg-state/slp/runtime")
        self.assertFalse(installation.runtime.exists())
        # Never silently abandon session state from an older checkout.
        (self.root / ".runtime").mkdir()
        with self.assertRaisesRegex(SlpError, "Legacy runtime"):
            Installation.load()

    def test_arbitrary_checkout_installs_and_launches_without_root_overrides(self):
        checkout = self.root / "arbitrary parent" / "renamed tool"
        shutil.copytree(ROOT / "scripts", checkout / "scripts",
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "config", checkout / "config", symlinks=True)
        fixture_home = self.root / "portable-home"
        fixture_home.mkdir()
        account = self.root / "selected-account"
        account.mkdir()
        env = dict(os.environ)
        for key in ("SLP_ROOT", "SLP_CONFIG_HOME", "SLP_RUNTIME_ROOT"):
            env.pop(key, None)
        env.update(HOME=str(fixture_home), XDG_CONFIG_HOME=str(fixture_home / "config base"),
                   XDG_STATE_HOME=str(fixture_home / "state base"),
                   PASEO_HOME=str(fixture_home / "paseo"),
                   SLP_PASEO_BIN=str(self.fake), CODEX_HOME=str(account))
        # Invoke entry points from outside the checkout, without SLP_ROOT.
        for command in ([str(checkout / "scripts/install")],
                        [str(checkout / "scripts/slp"), "paseo", "sync"]):
            result = subprocess.run(command, cwd=self.root, env=env,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((fixture_home / "config base/slp").resolve(), checkout / "config")
        self.assertEqual((fixture_home / ".local/bin/slp").resolve(), checkout / "scripts/slp")
        self.assertEqual((fixture_home / ".agents/skills/ponytail").resolve(),
                         checkout / "config/skills/ponytail")
        config = json.loads((fixture_home / "paseo/config.json").read_text())
        peer = config["agents"]["providers"]["slp-peer"]
        self.assertEqual(peer["env"]["SLP_ROOT"], str(checkout))
        runtime = fixture_home / "state base/slp/runtime"
        self.assertEqual(peer["env"]["SLP_RUNTIME_ROOT"], str(runtime))
        result = subprocess.run(peer["command"] + ["app-server"], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["home"], str(account))
        self.assertIn(str(checkout / "config"), (runtime / "codex/peer/role.md").read_text())
        self.assertFalse((checkout / ".runtime").exists())

    def test_installer_externalizes_state_and_snapshots_without_copying(self):
        os.environ.pop("SLP_RUNTIME_ROOT")
        fake_home = self.root / "home"
        database = self.root / ".runtime/codex/lead/state.sqlite"
        database.parent.mkdir(parents=True)
        database.write_bytes(b"session state")
        inode = database.stat().st_ino
        snapshot = self.root / "runtime/snapshots/codex/lead.json"
        snapshot.parent.mkdir(parents=True)
        snapshot.write_text('{"role":"lead"}')
        with patch.object(Path, "home", return_value=fake_home), contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / "scripts/install"))
            runpy.run_path(str(ROOT / "scripts/install"))
        installation = Installation.load()
        moved = installation.runtime / "codex/lead/state.sqlite"
        self.assertEqual(moved.read_bytes(), b"session state")
        self.assertEqual(moved.stat().st_ino, inode)
        self.assertEqual((installation.runtime.parent / "snapshots/codex/lead.json").read_text(), snapshot.read_text())
        self.assertTrue((self.root / ".runtime").is_symlink())
        self.assertEqual((fake_home / ".config/slp").resolve(), self.root / "config")

    def test_installer_preserves_private_skill_before_any_changes(self):
        fake_home = self.root / "home"
        private_skill = fake_home / ".agents/skills/ponytail"
        private_skill.mkdir(parents=True)
        manifest = private_skill / "SKILL.md"
        manifest.write_text("private user skill")
        with patch.object(Path, "home", return_value=fake_home), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(ROOT / "scripts/install"))
        self.assertEqual(manifest.read_text(), "private user skill")
        self.assertFalse((fake_home / ".config/slp").exists())
        self.assertFalse(self.installation.runtime.exists())

    def test_installer_refuses_conflicting_external_state_before_changes(self):
        os.environ.pop("SLP_RUNTIME_ROOT")
        legacy = self.root / ".runtime/codex/lead"
        legacy.mkdir(parents=True)
        (legacy / "state.sqlite").write_bytes(b"old state")
        destination = self.root / "xdg-state/slp/runtime"
        destination.mkdir(parents=True)
        (destination / "private").write_text("unrelated state")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runpy.run_path(str(ROOT / "scripts/install"))
        self.assertEqual((legacy / "state.sqlite").read_bytes(), b"old state")
        self.assertEqual((destination / "private").read_text(), "unrelated state")
        self.assertFalse((self.root / ".runtime").is_symlink())

    def test_all_roles_launch_through_their_generated_home(self):
        for role in self.installation.settings["roles"]:
            with self.subTest(role=role):
                result = self.run_cli(role, "app-server", "--flag=a b")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                runtime = self.installation.runtime / "codex" / role
                self.assertEqual(data, {"home": str(runtime), "args": ["app-server", "--flag=a b"]})
                config = tomllib.loads((runtime / "config.toml").read_text())
                self.assertIn(f"Role: {role.title()}.", config["developer_instructions"])
                self.assertFalse(config["features"]["multi_agent_v2"])
                self.assertFalse(config["features"]["multi_agent"])
                self.assertEqual(runtime.stat().st_mode & 0o777, 0o700)
                self.assertEqual((runtime / "auth.json").resolve(), self.canonical / "auth.json")

    def test_source_changes_regenerate_config_but_preserve_session_state(self):
        runtime = self.adapter.prepare(self.installation, self.provider, "lead")
        session = runtime / "sessions/private.jsonl"
        session.parent.mkdir()
        session.write_text("private session state")
        inode = session.stat().st_ino
        role = self.installation.config / "roles/lead.md"
        role.write_text(role.read_text() + "\nNew role rule.\n")
        self.adapter.prepare(self.installation, self.provider, "lead")
        self.assertIn("New role rule", (runtime / "role.md").read_text())
        self.assertEqual(session.read_text(), "private session state")
        self.assertEqual(session.stat().st_ino, inode)

    def test_multiline_base_instructions_and_nested_config_are_preserved(self):
        base = {"model": "gpt-6.1-sol", "developer_instructions": "Canonical\n[not a table]\n🐾",
                "projects": {"/path/with.dots": {"trust_level": "trusted"}},
                "features": {"multi_agent_v2": {"enabled": True}},
                "hooks": {"SessionEnd": [{"hooks": [{"type": "command", "command": "true"}]}]}}
        (self.canonical / "config.toml").write_text(dump_toml(base))
        runtime = self.adapter.prepare(self.installation, self.provider, "lead")
        config = tomllib.loads((runtime / "config.toml").read_text())
        self.assertTrue(config["developer_instructions"].startswith(base["developer_instructions"]))
        self.assertEqual(config["projects"], base["projects"])
        self.assertEqual(config["hooks"], base["hooks"])
        self.assertFalse(config["features"]["multi_agent_v2"]["enabled"])

    def test_invalid_base_does_not_modify_existing_runtime(self):
        runtime = self.adapter.prepare(self.installation, self.provider, "lead")
        before = (runtime / "config.toml").read_bytes()
        (self.canonical / "config.toml").write_text("broken config")
        with self.assertRaises(tomllib.TOMLDecodeError):
            self.adapter.prepare(self.installation, self.provider, "lead")
        self.assertEqual((runtime / "config.toml").read_bytes(), before)

    def test_private_auth_collision_is_rejected_before_writes(self):
        runtime = self.installation.runtime / "codex/lead"
        runtime.mkdir(parents=True)
        (runtime / "auth.json").write_text("private auth")
        with self.assertRaisesRegex(SlpError, "private non-symlink"):
            self.adapter.prepare(self.installation, self.provider, "lead")
        self.assertEqual((runtime / "auth.json").read_text(), "private auth")
        self.assertFalse((runtime / "config.toml").exists())

    def test_symlink_runtime_is_rejected(self):
        parent = self.installation.runtime / "codex"
        parent.mkdir(parents=True)
        (parent / "lead").symlink_to(self.canonical)
        with self.assertRaisesRegex(SlpError, "must not be a symlink"):
            self.adapter.prepare(self.installation, self.provider, "lead")

    def test_model_catalog_excludes_hidden_and_native_delegation_effort(self):
        report = self.adapter.catalog(self.installation, self.provider)
        self.assertEqual([m["id"] for m in report["models"]], ["gpt-6.1-sol", "other-model"])
        self.assertFalse(any(e["id"] == "ultra" for m in report["models"] for e in m["efforts"]))
        runtime = self.adapter.prepare(self.installation, self.provider, "lead")
        raw = json.loads((runtime / "model-catalog.no-native-agents.json").read_text())
        self.assertTrue(all(m["multi_agent_version"] is None for m in raw["models"]))

    def test_profiles_use_only_supported_pairs_and_preserve_unrelated_settings(self):
        existing = {"version": 1, "pluginsEnabled": True,
            "plugins": {"zerosub": {"source": "directory", "path": "/verified/plugin", "enabled": True}},
            "daemon": {"listen": "127.0.0.1:7777", "agentProfiles": [
            {"id": "personal", "name": "Personal", "provider": "codex"}]},
            "agents": {"providers": {"custom-user": {"extends": "claude", "label": "User"}}}}
        config, manifest, reports = paseo.build(self.installation, existing)
        self.assertEqual(config["daemon"]["listen"], "127.0.0.1:7777")
        self.assertEqual(config["plugins"], existing["plugins"])
        self.assertTrue(config["pluginsEnabled"])
        self.assertIn("custom-user", config["agents"]["providers"])
        self.assertEqual(config["daemon"]["agentProfiles"][0]["id"], "personal")
        # 2 supported shortcuts for the first model, 1 for the other; 3 roles.
        self.assertEqual(len(manifest["profiles"]), 9)
        valid = {(m["id"], e["id"]) for m in reports[0]["models"] for e in m["efforts"]}
        for profile in config["daemon"]["agentProfiles"][1:]:
            self.assertIn((profile["model"], profile["thinkingOptionId"]), valid)
            self.assertFalse(profile["name"].startswith("SLP"))
        peer = config["agents"]["providers"]["slp-peer"]
        self.assertEqual(peer["label"], "Peer")
        self.assertIn("create_agent", peer["paseoTools"]["disabledTools"])
        self.assertEqual(paseo.build(self.installation, config, manifest)[0], config)

    def test_sync_prunes_only_previously_owned_profiles(self):
        config, manifest, _ = paseo.build(self.installation, {"version": 1})
        old_id = next(pid for pid in manifest["profiles"] if pid.endswith("-xhigh"))
        self.installation.settings["profiles"]["efforts"] = ["high"]
        updated, next_manifest, _ = paseo.build(self.installation, config, manifest)
        self.assertNotIn(old_id, next_manifest["profiles"])
        self.assertNotIn(old_id, [p["id"] for p in updated["daemon"]["agentProfiles"]])

    def test_unknown_default_model_is_rejected_without_substitution(self):
        self.installation.settings["roles"]["lead"]["model"] = "unavailable"
        with self.assertRaisesRegex(SlpError, "absent"):
            self.adapter.prepare(self.installation, self.provider, "lead")

    def test_paseo_binary_version_probe_keeps_provider_identity(self):
        provider = {"id": "example", "enabled": True, "adapter": "prompt-argument", "extends": "claude",
                    "command": [str(self.fake)], "prompt_args": ["--prompt-file", "{prompt_file}"]}
        (self.installation.config / "providers/example.toml").write_text(dump_toml(provider))
        launcher = self.installation.write_launcher(provider)
        result = subprocess.run([str(launcher), "--version"], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["args"], ["--version"])

    def test_new_cli_provider_is_configuration_only(self):
        provider = {"id": "example", "enabled": True, "adapter": "prompt-argument", "extends": "claude",
                    "label": "Example", "command": [str(self.fake)],
                    "prompt_args": ["--append-system-prompt-file", "{prompt_file}"],
                    "model_args": ["--model", "{model}"], "effort_args": ["--effort", "{effort}"],
                    "models": [{"id": "example-model", "label": "Example", "default_effort": "high",
                                "efforts": [{"id": "high", "label": "High"}]}]}
        (self.installation.config / "providers/example.toml").write_text(dump_toml(provider))
        result = self.run_cli("--provider", "example", "peer", "-p", "bounded task")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(result.stdout)
        runtime = self.installation.runtime / "example/peer"
        self.assertEqual(args["args"], ["--append-system-prompt-file", str(runtime / "role.md"),
                                        "--model", "example-model", "--effort", "high", "-p", "bounded task"])
        self.assertIsNone(args["home"])
        self.assertIn("Role: Peer.", (runtime / "role.md").read_text())
        self.assertFalse((runtime / "config.toml").exists())

    def test_invalid_candidate_does_not_touch_paseo_configuration(self):
        directory = self.root / "paseo"
        directory.mkdir()
        config = directory / "config.json"
        original = '{"version":1}'
        config.write_text(original)
        os.environ["PASEO_HOME"] = str(directory)
        with patch.object(paseo, "validate", side_effect=SlpError("schema rejected")):
            with self.assertRaises(SlpError):
                paseo.sync(self.installation)
        self.assertEqual(config.read_text(), original)
        self.assertFalse(self.installation.runtime.exists())

    def test_installer_preserves_legacy_sessions_and_is_repeatable(self):
        fake_home = self.root / "home"
        old_config = fake_home / ".config/slp"
        (old_config / "overlays").mkdir(parents=True)
        (old_config / "workflow").mkdir()
        (old_config / "workflow/WORKSPACE_PROTOCOL.md").write_text("old contract")
        old_runtime = self.installation.runtime / "lead"
        old_runtime.mkdir(parents=True)
        database = old_runtime / "state.sqlite"
        database.write_bytes(b"preserve existing database")
        inode = database.stat().st_ino
        with patch.object(Path, "home", return_value=fake_home), contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / "scripts/install"))
            runpy.run_path(str(ROOT / "scripts/install"))
        new_database = self.installation.runtime / "codex/lead/state.sqlite"
        self.assertEqual(new_database.read_bytes(), b"preserve existing database")
        self.assertEqual(new_database.stat().st_ino, inode)
        self.assertTrue(old_runtime.is_symlink())
        self.assertEqual(old_config.resolve(), self.root / "config")
        self.assertTrue((fake_home / ".local/bin/slp").is_symlink())
        self.assertEqual(len(list((self.root / "xdg-state/slp/backups").glob("layout-*"))), 1)

    def enable_zerosub(self):
        self.provider["account_routing"] = "zerosub"
        path = self.installation.config / "providers/codex.toml"
        path.write_text(dump_toml(self.provider))

    def test_zerosub_keeps_selected_home_and_loads_role_as_overrides(self):
        self.enable_zerosub()
        account = self.root / "account-b"
        account.mkdir()
        auth = account / "auth.json"
        auth.write_text('{"test_account":"B"}')
        before = auth.read_bytes()
        os.environ["CODEX_HOME"] = str(account)
        os.environ["CODEX_SQLITE_HOME"] = str(self.root / "zerosub-shared-state")
        result = self.run_cli("lead", "app-server")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["home"], str(account))
        args = data["args"]
        overrides = {}
        while args and args[0] == "-c":
            key, value = args[1].split("=", 1)
            overrides[key] = tomllib.loads("value = " + value)["value"]
            args = args[2:]
        self.assertEqual(args, ["app-server"])
        self.assertIn("Role: Lead.", overrides["developer_instructions"])
        self.assertEqual(overrides["sqlite_home"], str(self.installation.runtime / "codex/lead"))
        self.assertFalse(overrides["features.multi_agent_v2"])
        self.assertEqual(auth.read_bytes(), before)
        self.assertFalse((self.installation.runtime / "codex/lead/auth.json").exists())

    def test_zerosub_can_route_every_role_to_two_different_accounts(self):
        self.enable_zerosub()
        for account_name in ("account-a", "account-b"):
            account = self.root / account_name
            account.mkdir()
            os.environ["CODEX_HOME"] = str(account)
            for role in self.installation.settings["roles"]:
                result = self.run_cli(role, "app-server")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["home"], str(account))

    def test_zerosub_provider_entries_do_not_opt_out_of_routing(self):
        self.enable_zerosub()
        config, _, _ = paseo.build(self.installation, {"version": 1})
        for definition in config["agents"]["providers"].values():
            self.assertEqual(definition["extends"], "codex")
            own_auth = ("CODEX_HOME", "OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")
            self.assertFalse(any(definition["env"].get(key) for key in own_auth))

    def test_zerosub_preserves_private_legacy_auth_and_session_state(self):
        self.enable_zerosub()
        runtime = self.installation.runtime / "codex/lead"
        runtime.mkdir(parents=True)
        auth = runtime / "auth.json"
        auth.write_text("private legacy auth")
        database = runtime / "state.sqlite"
        database.write_bytes(b"legacy SQLite state")
        self.adapter.prepare(self.installation, self.provider, "lead")
        self.assertEqual(auth.read_text(), "private legacy auth")
        self.assertEqual(database.read_bytes(), b"legacy SQLite state")

    def test_zerosub_preparation_saves_config_but_does_not_claim_installation(self):
        self.enable_zerosub()
        directory = self.root / "paseo"
        directory.mkdir()
        (directory / "config.json").write_text('{"version":1}')
        os.environ["PASEO_HOME"] = str(directory)
        namespace = runpy.run_path(str(ROOT / "scripts/setup-zerosub"), run_name="setup_test")
        with patch.object(Path, "home", return_value=self.root / "fake-home"), \
             patch.object(paseo, "validate"), contextlib.redirect_stdout(io.StringIO()):
            config, preference_file = namespace["prepare"](self.installation)
        persisted = json.loads((directory / "config.json").read_text())
        self.assertTrue(persisted["pluginsEnabled"])
        self.assertNotIn("zerosub", persisted.get("plugins", {}))
        self.assertEqual(config["version"], "1.3.0")
        preferences = json.loads(preference_file.read_text())
        self.assertTrue(preferences["autoSwitch"])
        self.assertFalse(preferences["autoRedeem"])
        self.assertFalse(preferences["forkOtherProvider"])
        self.assertFalse((self.installation.runtime / "zerosub-installation.json").exists())

    def test_zerosub_preferences_use_revision_and_preserve_unrelated_settings(self):
        module = (ROOT / "scripts/lib/zerosub-settings.mjs").as_uri()
        source = '''
import assert from 'node:assert/strict';
const {applyPreferences} = await import(process.argv[1]);
let writes = 0;
const client = {async invokePluginRpc(id, method, input) {
 assert.equal(id, 'zerosub');
 if (method.endsWith('.read')) return {status:'ready', revision:'current-revision', values:{autoSwitch:false, autoRedeem:true, extraSetting:17}};
 writes++;
 assert.equal(input.revision, 'current-revision');
 assert.equal(input.values.extraSetting, 17);
 return {status:'saved', values:input.values};
}};
const saved = await applyPreferences(client, {autoSwitch:true,autoRedeem:false});
assert.equal(saved.autoRedeem, false);
assert.equal(writes, 1);
await assert.rejects(()=>applyPreferences(client,{unsupportedSetting:true}));
assert.equal(writes, 1);
'''
        result = subprocess.run(["node", "--input-type=module", "-e", source, module],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
