# Golden transaction vectors

One space-separated transaction per line (no header):
`primary target previous slow adapt gate row_start threshold packed_refs expected_data expected_prediction expected_error expected_flag`.

All scalar fields are decimal signed codes except threshold (unsigned) and packed_refs (hex, tap/pixel 0 in least significant word). W=16, FRAC=12. A, C, D, E, F use the pre-update prediction and target-minus-prediction error; B uses the post-estimate bias or applied bias as prediction, zero as the unused error, and flag=1 for apply transactions. All other flags are zero except D gated replacements. Unused fields are zero or ignored. See the [fixed-point model](../model/fixed_model.py) for independent replay and [architecture specification](../README.md).
