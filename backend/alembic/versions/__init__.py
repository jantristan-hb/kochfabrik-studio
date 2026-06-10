# Markiert backend/alembic/versions/ als regulaeres Package (statt
# Namespace-Package). Ohne diese Datei ist __file__ des importierten
# Package None -> os.path.dirname(__file__) wirft TypeError
# (siehe test_sprint2.py::test_alembic_baseline_present_and_empty).
