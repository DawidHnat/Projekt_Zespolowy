import os
import shutil
import subprocess
import sys
import tempfile
import unittest

# Dodaj infra/deploy do sys.path, aby zaimportować validate_release
infra_deploy_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "infra", "deploy")
)
sys.path.insert(0, infra_deploy_dir)
import validate_release as vr  # noqa: E402


class ValidateReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_vr_")
        self.repo_dir = os.path.join(self.temp_dir, "test_repo.git")

        # Inicjalizacja bare repo
        subprocess.run(["git", "init", "--bare", self.repo_dir], check=True, capture_output=True)

        # Przygotowanie repo roboczego do stworzenia historii commitów
        self.work_dir = os.path.join(self.temp_dir, "work")
        subprocess.run(["git", "init", self.work_dir], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "config", "user.name", "Test Committer"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", self.work_dir, "config", "user.email", "test@fleet-flow.local"],
            check=True,
            capture_output=True,
        )

        # Commit A
        file_a = os.path.join(self.work_dir, "file.txt")
        with open(file_a, "w") as f:
            f.write("Commit A\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Commit A"],
            check=True,
            capture_output=True,
        )
        self.sha_a = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

        # Commit B (potomek A)
        with open(file_a, "a") as f:
            f.write("Commit B\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Commit B"],
            check=True,
            capture_output=True,
        )
        self.sha_b = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

        # Commit C (potomek B)
        with open(file_a, "a") as f:
            f.write("Commit C\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Commit C"],
            check=True,
            capture_output=True,
        )
        self.sha_c = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

        # Push gałęzi main do bare repo
        subprocess.run(
            ["git", "-C", self.work_dir, "remote", "add", "origin", self.repo_dir],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", self.work_dir, "push", "origin", "HEAD:refs/heads/main"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_first_deployment_without_current_sha_passes(self):
        code, msg = vr.validate_release(
            target_sha=self.sha_a,
            current_sha=None,
            repo_dir=self.repo_dir,
            offline=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("Pierwsze wdrożenie", msg)

    def test_idempotent_retry_of_current_sha_passes(self):
        code, msg = vr.validate_release(
            target_sha=self.sha_b,
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            offline=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("idempotentne", msg)

    def test_forward_release_from_b_to_c_passes(self):
        code, msg = vr.validate_release(
            target_sha=self.sha_c,
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            offline=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("ZATWIERDZONO", msg)

    def test_stale_commit_a_rejected_when_b_is_active(self):
        """SCRUM-137: Re-run historycznego CI z commitem A nie może cofnąć serwera z B do A."""
        code, msg = vr.validate_release(
            target_sha=self.sha_a,
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            allow_rollback=False,
            offline=True,
        )
        self.assertEqual(code, 1)
        self.assertIn("ODRZUCONO", msg)
        self.assertIn("przestarzałego", msg)

    def test_deliberate_rollback_from_b_to_a_allowed_with_flag(self):
        """Celowy rollback do commita A za jawną zgodą operatora jest dozwolony."""
        code, msg = vr.validate_release(
            target_sha=self.sha_a,
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            allow_rollback=True,
            offline=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("ROLLBACK", msg)
        self.assertIn("zatwierdzony przez operatora", msg)

    def test_divergent_commit_rejected_without_rollback_flag(self):
        # Utwórz gałąź boczną od A
        subprocess.run(
            ["git", "-C", self.work_dir, "checkout", "-b", "feature", self.sha_a],
            check=True,
            capture_output=True,
        )
        divergent_file = os.path.join(self.work_dir, "feature.txt")
        with open(divergent_file, "w") as f:
            f.write("Divergent\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Divergent"],
            check=True,
            capture_output=True,
        )
        sha_divergent = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )
        subprocess.run(
            ["git", "-C", self.work_dir, "push", "origin", "HEAD:refs/heads/feature"],
            check=True,
            capture_output=True,
        )

        code, msg = vr.validate_release(
            target_sha=sha_divergent,
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            allow_rollback=False,
            offline=True,
        )
        self.assertEqual(code, 1)
        self.assertIn("ODRZUCONO", msg)

    def test_invalid_sha_rejected(self):
        code, msg = vr.validate_release(
            target_sha="not-a-sha",
            current_sha=self.sha_b,
            repo_dir=self.repo_dir,
            offline=True,
        )
        self.assertEqual(code, 1)
        self.assertIn("Niepoprawny format SHA", msg)


class DeploymentSimulatorTests(unittest.TestCase):
    """Izolowany symulator cyklu wdrożenia i odrzucenia starego wydania bez mutacji."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_sim_")
        self.base_dir = os.path.join(self.temp_dir, "opt", "fleet-flow")
        self.shared_dir = os.path.join(self.base_dir, "shared")
        self.releases_dir = os.path.join(self.base_dir, "releases")
        os.makedirs(self.shared_dir, exist_ok=True)
        os.makedirs(self.releases_dir, exist_ok=True)

        self.repo_dir = os.path.join(self.shared_dir, "repo.git")
        subprocess.run(["git", "init", "--bare", self.repo_dir], check=True, capture_output=True)

        # Repozytorium robocze
        self.work_dir = os.path.join(self.temp_dir, "work")
        subprocess.run(["git", "init", self.work_dir], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "config", "user.name", "CI Robot"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", self.work_dir, "config", "user.email", "ci@fleet-flow.local"],
            check=True,
            capture_output=True,
        )

        # Commit A
        file_txt = os.path.join(self.work_dir, "app.txt")
        with open(file_txt, "w") as f:
            f.write("App Version A\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Release A"],
            check=True,
            capture_output=True,
        )
        self.sha_a = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

        # Commit B
        with open(file_txt, "w") as f:
            f.write("App Version B\n")
        subprocess.run(["git", "-C", self.work_dir, "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", self.work_dir, "commit", "-m", "Release B"],
            check=True,
            capture_output=True,
        )
        self.sha_b = (
            subprocess.check_output(["git", "-C", self.work_dir, "rev-parse", "HEAD"])
            .decode()
            .strip()
        )

        # Push main
        subprocess.run(
            ["git", "-C", self.work_dir, "remote", "add", "origin", self.repo_dir],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", self.work_dir, "push", "origin", "HEAD:refs/heads/main"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def simulate_deploy(self, revision: str, env_content: str, allow_rollback: bool = False):
        """Symulator kroków fleet-flow-deploy."""
        current_symlink = os.path.join(self.base_dir, "current")
        current_commit = None
        if os.path.islink(current_symlink) or os.path.exists(current_symlink):
            commit_file = os.path.join(current_symlink, "commit")
            if os.path.exists(commit_file):
                with open(commit_file) as f:
                    current_commit = f.read().strip()

        # Krok walidacji
        code, msg = vr.validate_release(
            target_sha=revision,
            current_sha=current_commit,
            repo_dir=self.repo_dir,
            allow_rollback=allow_rollback,
            offline=True,
        )
        if code != 0:
            return code, msg

        # Wdrożenie: tworzenie katalogu wydania
        rel_dir = os.path.join(self.releases_dir, f"{revision}.simulated")
        os.makedirs(rel_dir, exist_ok=True)
        with open(os.path.join(rel_dir, "commit"), "w") as f:
            f.write(revision + "\n")

        # Aktualizacja runtime.env
        env_file = os.path.join(self.shared_dir, "runtime.env")
        with open(env_file, "w") as f:
            f.write(env_content)

        # Podmiana symlinku current
        temp_link = os.path.join(self.base_dir, f".current-{revision}")
        if os.path.lexists(temp_link):
            os.remove(temp_link)
        os.symlink(rel_dir, temp_link)
        os.replace(temp_link, current_symlink)

        return 0, "OK"

    def test_stale_deploy_attempt_causes_no_mutation(self):
        """Wdrożenie B, próba starego A odrzucona bez mutacji, ponowienie B dozwolone."""
        # 1. Wdrożenie wersji B
        code, _ = self.simulate_deploy(self.sha_b, "APP_ENV=VERSION_B")
        self.assertEqual(code, 0)

        current_link = os.path.join(self.base_dir, "current")
        self.assertEqual(
            os.path.realpath(current_link),
            os.path.realpath(os.path.join(self.releases_dir, f"{self.sha_b}.simulated")),
        )
        env_file = os.path.join(self.shared_dir, "runtime.env")
        with open(env_file) as f:
            self.assertEqual(f.read().strip(), "APP_ENV=VERSION_B")

        # 2. Próba wdrożenia starej wersji A (symulacja ponowienia starego CI)
        code_stale, msg_stale = self.simulate_deploy(self.sha_a, "APP_ENV=STALE_VERSION_A")
        self.assertEqual(code_stale, 1)
        self.assertIn("ODRZUCONO", msg_stale)

        # WERYFIKACJA BRAKU MUTACJI:
        # Link current nadal wskazuje na B
        self.assertEqual(
            os.path.realpath(current_link),
            os.path.realpath(os.path.join(self.releases_dir, f"{self.sha_b}.simulated")),
        )
        # runtime.env nadal ma treść z wersji B
        with open(env_file) as f:
            self.assertEqual(f.read().strip(), "APP_ENV=VERSION_B")
        # Żaden katalog dla wydania A nie powstał
        self.assertFalse(os.path.exists(os.path.join(self.releases_dir, f"{self.sha_a}.simulated")))

        # 3. Ponowienie wersji B jest dozwolone i idempotentne
        code_retry, msg_retry = self.simulate_deploy(self.sha_b, "APP_ENV=VERSION_B")
        self.assertEqual(code_retry, 0)
        with open(env_file) as f:
            self.assertEqual(f.read().strip(), "APP_ENV=VERSION_B")

        # 4. Celowy rollback do wersji A z flagą jest dozwolony
        code_rb, msg_rb = self.simulate_deploy(
            self.sha_a, "APP_ENV=VERSION_A_ROLLBACK", allow_rollback=True
        )
        self.assertEqual(code_rb, 0)
        self.assertEqual(
            os.path.realpath(current_link),
            os.path.realpath(os.path.join(self.releases_dir, f"{self.sha_a}.simulated")),
        )
        with open(env_file) as f:
            self.assertEqual(f.read().strip(), "APP_ENV=VERSION_A_ROLLBACK")


if __name__ == "__main__":
    unittest.main()
