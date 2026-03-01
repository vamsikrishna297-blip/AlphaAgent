import os
from pathlib import Path

import qlib
from dotenv import load_dotenv

# When running this script directly, load .env from both CWD and project root.
load_dotenv()  # CWD/.env
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

provider_uri_raw = os.getenv("QLIB_PROVIDER_URI") or os.getenv("QLIB_DEFAULT_DATA_DIR")
if not provider_uri_raw:
    raise RuntimeError(
        "QLIB_PROVIDER_URI is not set. Please set it in .env or shell, e.g. "
        "QLIB_PROVIDER_URI=~/.qlib/qlib_data/in_data",
    )

provider_uri = Path(provider_uri_raw).expanduser().resolve()
if not provider_uri.exists():
    raise RuntimeError(
        f"QLIB_PROVIDER_URI path does not exist: {provider_uri}. "
        "Please point it to your qlib-formatted data directory (contains calendars/features/instruments).",
    )

print(f"[generate.py] Using QLIB_PROVIDER_URI={provider_uri}")
qlib.init(provider_uri=str(provider_uri))
from qlib.data import D

instruments = D.instruments()
fields = ["$open", "$close", "$high", "$low", "$volume"]  # , "$amount", "$turn", "$pettm", "$pbmrq"
data = D.features(instruments, fields, freq="day").swaplevel().sort_index().loc["2015-01-01":].sort_index()

# 计算收益率
data["$return"] = data.groupby(level=0)["$close"].pct_change().fillna(0)

print(data)

data.to_hdf("./daily_pv_all.h5", key="data")

fields = ["$open", "$close", "$high", "$low", "$volume"]  # , "$amount", "$turn", "$pettm", "$pbmrq"
data = (
    (
        D.features(instruments, fields, freq="day")
        .swaplevel()
        .sort_index()
    )
    .swaplevel()
    .loc[data.reset_index()["instrument"].unique()[:100]]
    .swaplevel()
    .sort_index()
)

# 计算收益率
data["$return"] = data.groupby(level=0)["$close"].pct_change().fillna(0)
print(data)
data.to_hdf("./daily_pv_debug.h5", key="data")
