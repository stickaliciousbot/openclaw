#!/usr/bin/env python3
import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from critical_apply_contracts import NpmBaseClassification, StagingDirClassification, sha256_file  # noqa: E402
from critical_apply_plugins.openclaw_npm_package import (  # noqa: E402
    PackageAuthority,
    create_restore_point_skeleton,
    decide_recovery,
    inspect_package_root,
    inspect_package_tar,
    inspect_speech_surface,
    inspect_staging_dirs,
    RestorePoint,
)


class OpenClawNpmPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="openclaw-npm-plugin-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def make_root(self, complete=True):
        root = self.tmp / "openclaw"
        (root / "dist/extensions/speech-core").mkdir(parents=True)
        (root / "dist/cli").mkdir(parents=True)
        (root / "dist/plugins").mkdir(parents=True)
        (root / "dist/control-ui/assets").mkdir(parents=True)
        (root / "package.json").write_text(json.dumps({"name": "openclaw", "version": "2026.5.7", "bin": {"openclaw": "openclaw.mjs"}}))
        (root / "openclaw.mjs").write_text("#!/usr/bin/env node\n")
        (root / "dist/index.js").write_text("export const ok = true;\n")
        (root / "dist/build-info.json").write_text(json.dumps({"sourceCommit": "abc1234567"}))
        (root / "dist/cli/gateway-lifecycle.runtime.js").write_text("export {};\n")
        (root / "dist/plugins/public-surface-runtime.js").write_text("export {};\n")
        (root / "dist/control-ui/index.html").write_text("<html></html>\n")
        if complete:
            (root / "dist/extensions/speech-core/runtime-api.js").write_text("export const runtimeApi = true;\n")
        return root

    def test_package_root_classifier_matrix(self):
        missing = self.tmp / "missing"
        self.assertEqual(inspect_package_root(missing)["classification"], NpmBaseClassification.NPM_BASE_MISSING.value)
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(inspect_package_root(empty)["classification"], NpmBaseClassification.NPM_BASE_EMPTY.value)
        incomplete = self.make_root(complete=False)
        self.assertEqual(inspect_package_root(incomplete, "2026.5.7", "abc1234567")["classification"], NpmBaseClassification.NPM_BASE_INCOMPLETE.value)
        shutil.rmtree(incomplete)
        complete = self.make_root(complete=True)
        self.assertEqual(inspect_package_root(complete, "2026.5.7", "abc1234567")["classification"], NpmBaseClassification.NPM_BASE_COHERENT.value)

    def test_speech_surface_import_chain(self):
        root = self.make_root(complete=True)
        runtime = root / "dist/extensions/speech-core/runtime-api.js"
        self.assertEqual(inspect_speech_surface(runtime)["classification"], "SPEECH_PUBLIC_SURFACE_COMPLETE")
        runtime.write_text("export {x} from './missing.js';\n")
        self.assertEqual(inspect_speech_surface(runtime)["classification"], "SPEECH_PUBLIC_SURFACE_IMPORT_MISSING")

    def test_staging_classifier(self):
        nm = self.tmp / "node_modules"
        nm.mkdir()
        self.assertEqual(inspect_staging_dirs(nm, pids=[])["classification"], StagingDirClassification.NONE.value)
        (nm / ".openclaw-abc123").mkdir()
        self.assertEqual(inspect_staging_dirs(nm, pids=[])["classification"], StagingDirClassification.INACTIVE_CAN_QUARANTINE.value)
        os.symlink("/tmp", nm / ".openclaw-badlink")
        self.assertEqual(inspect_staging_dirs(nm, pids=[])["classification"], StagingDirClassification.SUSPICIOUS_BLOCK.value)

    def test_tar_authority_validation(self):
        root = self.make_root(complete=True)
        package_dir = self.tmp / "package"
        shutil.copytree(root, package_dir)
        tgz = self.tmp / "openclaw.tgz"
        with tarfile.open(tgz, "w:gz") as tf:
            tf.add(package_dir, arcname="package")
        details = inspect_package_tar(tgz)
        self.assertEqual(details["package_json"]["name"], "openclaw")
        authority = PackageAuthority(str(tgz), sha256_file(tgz), "2026.5.7", "abc1234567")
        self.assertTrue(authority.verify().ok)
        bad = PackageAuthority(str(tgz), "0" * 64, "2026.5.7", "abc1234567")
        self.assertFalse(bad.verify().ok)

    def test_restore_point_skeleton_and_decision(self):
        restore_root = self.tmp / "restore"
        manifest = create_restore_point_skeleton(restore_root)
        rp = RestorePoint(str(restore_root), manifest["created_at_epoch"])
        self.assertTrue(rp.verify().ok)
        missing_health = {"classification": NpmBaseClassification.NPM_BASE_MISSING.value}
        staging = {"classification": StagingDirClassification.NONE.value}
        decision = decide_recovery(missing_health, staging, rp.verify())
        self.assertEqual(decision["terminal"], "ROLLBACK_REQUIRED")


if __name__ == "__main__":
    unittest.main()
