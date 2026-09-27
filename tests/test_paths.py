from xenosite.xmet import data_dir, ontology_yaml, repo_root


def test_ontology_yaml_exists():
    assert repo_root().name.startswith("xenosite-xmet")
    assert ontology_yaml().is_file()
    assert (data_dir() / "ontology" / "xmet.skos.jsonld").is_file()
