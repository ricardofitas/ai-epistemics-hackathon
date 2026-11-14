"""Align gold with the native trim operation when every option is preserved."""
import copy


def align_preserved_options(record, source_options, source_gold_position):
    result = copy.deepcopy(record)
    native_options = record.get('choices')
    if native_options == [option.strip() for option in source_options]:
        result['correct_text'] = source_options[source_gold_position].strip()
        result['expected_reference'] = chr(65 + source_gold_position)
    return result
