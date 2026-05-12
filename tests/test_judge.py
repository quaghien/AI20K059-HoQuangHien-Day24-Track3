from src.judge import parse_absolute_output, parse_pairwise_output


def test_parse_pairwise_output_strips_code_fence():
    text = '```json\n{"winner":"A","reason":"ok"}\n```'
    parsed = parse_pairwise_output(text)
    assert parsed["winner"] == "A"


def test_parse_absolute_output_has_default_overall():
    parsed = parse_absolute_output('{"accuracy":4,"relevance":5,"conciseness":3,"helpfulness":4}')
    assert parsed["overall"] == 4.0
