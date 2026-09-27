"""Tests for centralized configuration loading and validation."""

from pathlib import Path
import tempfile
import unittest

from src.config import load_config


class ConfigurationTests(unittest.TestCase):
    def test_default_configuration_is_complete_and_frozen_values_are_explicit(self):
        config = load_config(environ={})

        self.assertEqual(Path("~/prototype-data/corpus").expanduser(), config.corpus_root)
        self.assertEqual("cpu", config.device)
        self.assertEqual(384, config.embedding_dimensions)
        self.assertEqual(256, config.max_tokens)
        self.assertEqual(50, config.retrieval_k)
        self.assertEqual(60, config.rrf_constant)

    def test_environment_overrides_yaml_values(self):
        config = load_config(environ={
            "PROTOTYPE_DATA_ROOT": "C:/external/prototype",
            "PROTOTYPE_CORPUS_ROOT": "C:/external/corpus",
            "PROTOTYPE_OFFLINE": "false",
            "PROTOTYPE_RETRIEVAL_K": "25",
        })

        self.assertEqual(Path("C:/external/prototype"), config.data_root)
        self.assertEqual(Path("C:/external/corpus"), config.corpus_root)
        self.assertEqual(Path("C:/external/prototype/validation"), config.validation_output)
        self.assertEqual(Path("C:/external/prototype/model-cache"), config.embedding_model_cache)
        self.assertFalse(config.offline)
        self.assertEqual(25, config.retrieval_k)

    def test_custom_yaml_is_loaded_before_environment_overrides(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "config.yaml"
            path.write_text(
                "data_root: C:/custom\n"
                "corpus_root: C:/custom/corpus\n"
                "validation_output: C:/custom/validation\n"
                "embedding_model_cache: C:/custom/cache\n"
                "offline: true\n"
                "device: cpu\n"
                "embedding_model_id: sentence-transformers/all-MiniLM-L6-v2\n"
                "embedding_model_revision: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41\n"
                "embedding_dimensions: 384\nmax_tokens: 256\n"
                "retrieval_k: 10\nrrf_constant: 60\n",
                encoding="utf-8",
            )

            config = load_config(path, environ={"PROTOTYPE_RETRIEVAL_K": "20"})

        self.assertEqual(Path("C:/custom"), config.data_root)
        self.assertEqual(20, config.retrieval_k)

    def test_invalid_values_fail_with_actionable_messages(self):
        for key, value, message in (
            ("PROTOTYPE_OFFLINE", "sometimes", "offline must be a boolean"),
            ("PROTOTYPE_DEVICE", "cuda", "device must be 'cpu'"),
            ("PROTOTYPE_EMBEDDING_DIMENSIONS", "128", "embedding_dimensions must remain 384"),
            ("PROTOTYPE_EMBEDDING_MODEL_REVISION", "short", "full 40-character SHA-1"),
            ("PROTOTYPE_RETRIEVAL_K", "0", "retrieval_k must be a positive integer"),
        ):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                load_config(environ={key: value})

    def test_missing_configuration_file_is_reported(self):
        with self.assertRaisesRegex(ValueError, "Cannot read configuration file"):
            load_config("C:/does-not-exist/prototype.yaml")

    def test_malformed_yaml_identifies_the_configuration_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "broken.yaml"
            path.write_text("data_root: [\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Cannot parse YAML configuration file"):
                load_config(path, environ={})


if __name__ == "__main__":
    unittest.main()