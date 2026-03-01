import os
from pathlib import Path

import qlib
from dotenv import load_dotenv

# When running this script directly, load project .env so QLIB_PROVIDER_URI is picked up.
load_dotenv(Path(__file__).resolve().parents[4] / ".env")

provider_uri = Path(os.getenv("QLIB_PROVIDER_URI", "~/.qlib/qlib_data/cn_data")).expanduser()
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
