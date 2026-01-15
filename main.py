import json

from gen.sentiment_gen import gen_sentiment_alphas
from svc.datafields import get_single_set_fields

if __name__ == "__main__":
    # gen_sentiment_alphas()

    fields = get_single_set_fields(dataset='pv30', delay=1, instrument_type='EQUITY', region='IND', universe='TOP500', typs=['GROUP'])
    # print(json.dumps(fields, indent=4, ensure_ascii=False))
    field_names = fields.keys()
    print(len(field_names))
    print(field_names)