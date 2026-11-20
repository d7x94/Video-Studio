# Mã suy luận FireRedLID (chép nguyên bản, không sửa)

- Nguồn: [FireRedTeam/FireRedASR2S](https://github.com/FireRedTeam/FireRedASR2S), thư mục `fireredasr2s/fireredlid`, commit `4e7d9aaf4482a47cec1724807026b9b151926eb5`.
- Giấy phép: Apache-2.0, Copyright 2026 Xiaohongshu (bản đầy đủ ở `references/LICENSE-firered.txt`, khớp từng byte với `LICENSE` của repo gốc ở commit trên).
- Dùng cho: `scripts/nhan_dang_lid.py` (chạy bởi `chep_loi_goc.py --lid`). Cần `torch`, `kaldiio`, `kaldi_native_fbank` (`setup.sh --lid`).
- Chỉ chép phần cần để suy luận. Không chép `speech2lang.py` (dòng lệnh), `utils/io.py` và `README.md`.
- Không sửa file nào. Chỗ cần khác bản gốc (nạp checkpoint bằng `mmap` để không tràn RAM) làm ở `nhan_dang_lid.py`.
- CI không chạy ruff trên thư mục này (mã gốc có vài biến, import không dùng).

sha256 từng file:

```
4a86be20fbea763a988215fa0d6f2f0cc6b9d42d5b38275a4b9b08cc93d681c9  __init__.py
a2753c33c43f2a095ea51a82f0d7a2a57212cf2a77d01bc16f704e6754f3164f  data/feat.py
8b58afea015bd60f8d958be602871e2be24b1aa4b341178b19d2799e82c7db51  data/token_dict.py
959501f2487792cae5266eea574b0c3be65de737e87159f2150d463dec7e2440  lid.py
8b2744d7932c19ddfe1df561b8b855a5cbc296d9bacfa086b38238574f530030  models/fireredlid_aed.py
d741910f080c7011f3ff2333fb6193d5b3822017e65cb7d1d5386db4d01aeba0  models/module/conformer_encoder.py
abaa7b9693427e4bc4644806dad4973e624a2e76164d23469ffa94f2f8a60265  models/module/transformer_decoder.py
8589dcada1cef58af3af2628499d0ec26e5470cdcc0130f642a35e8a28dffdf4  models/param.py
54d58c0fc086ca4cf26459eec9b537c5e478d31a59b27432fed89f6a3978b53a  tokenizer/lid_tokenizer.py
```
