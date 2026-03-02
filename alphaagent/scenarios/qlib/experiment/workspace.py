from pathlib import Path
import os
import re
from typing import Any

import pandas as pd

from alphaagent.core.experiment import FBWorkspace
from alphaagent.log import logger
from alphaagent.utils.env import QTDockerEnv


class QlibFBWorkspace(FBWorkspace):
    def __init__(self, template_folder_path: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.inject_code_from_folder(template_folder_path)

    def execute(
        self, 
        qlib_config_name: str = "conf.yaml", 
        run_env: dict = {}, 
        use_local: bool = True, 
        *args, 
        **kwargs
    ) -> str:
        # 使用本地环境或Docker环境
        qtde = QTDockerEnv(is_local=use_local)
        qtde.prepare()
        
        config_path = self.workspace_path / qlib_config_name
        if config_path.exists():
            config_text = config_path.read_text()

            # qlib only supports built-in regions (cn/us/tw); guard stale templates still using region: in
            if re.search(r"(^|\n)\s*region:\s*in\s*(\n|$)", config_text):
                config_text = re.sub(r"(^|\n)(\s*region:\s*)in(\s*(?:\n|$))", r"\1\2cn\3", config_text, count=1)
                logger.warning(
                    f"Detected unsupported qlib region='in' in {config_path.name}; auto-corrected to region='cn'. "
                    "Keep provider_uri/instruments pointing to India data."
                )

            # Optional market override from env to match available instrument files
            qlib_market = os.getenv("QLIB_MARKET", "").strip()
            qlib_benchmark = os.getenv("QLIB_BENCHMARK", "").strip()
            if qlib_market:
                config_text = re.sub(
                    r"(^|\n)(\s*market:\s*&market\s*)[^\n]+",
                    rf"\1\2{qlib_market}",
                    config_text,
                    count=1,
                )
            if qlib_benchmark:
                config_text = re.sub(
                    r"(^|\n)(\s*benchmark:\s*&benchmark\s*)[^\n]+",
                    rf"\1\2{qlib_benchmark}",
                    config_text,
                    count=1,
                )

            # Validate instrument file exists for selected market in provider_uri
            provider_match = re.search(r'(^|\n)\s*provider_uri:\s*"?([^\n"]+)"?', config_text)
            market_match = re.search(r"(^|\n)\s*market:\s*&market\s*([^\n#]+)", config_text)
            if provider_match and market_match:
                provider_uri = Path(os.path.expanduser(provider_match.group(2).strip())).resolve()
                market_name = market_match.group(2).strip()
                instrument_path = provider_uri / "instruments" / f"{market_name.lower()}.txt"
                if not instrument_path.exists():
                    available = sorted([x.name for x in (provider_uri / "instruments").glob("*.txt")]) if (provider_uri / "instruments").exists() else []
                    raise RuntimeError(
                        f"Instrument file not found for market '{market_name}': {instrument_path}. "
                        f"Set QLIB_MARKET to one of available instrument files (without .txt), e.g. {available[:10]}"
                    )

            config_path.write_text(config_text)

        # 运行Qlib回测
        logger.info(f"Execute {'Local' if use_local else 'Docker container'} Backtest: qrun {qlib_config_name}")
        execute_log = qtde.run(
            local_path=str(self.workspace_path),
            entry=f"qrun {qlib_config_name}",
            env=run_env,
        )

        # 处理结果
        logger.info(f"Read {'Local' if use_local else 'Docker container'} Backtest Result")
        execute_log = qtde.run(
            local_path=str(self.workspace_path),
            entry="python read_exp_res.py",
            env=run_env,
        )

        # 加载结果
        ret_path = self.workspace_path / "ret.pkl"
        csv_path = self.workspace_path / "qlib_res.csv"

        if not ret_path.exists() or not csv_path.exists():
            raise RuntimeError(
                "Qlib backtest did not produce expected output artifacts (ret.pkl / qlib_res.csv). "
                f"Config={qlib_config_name}, workspace={self.workspace_path}. "
                "A common reason is market-config mismatch (e.g., India provider with CN config), "
                "or setting unsupported qlib region='in' (qlib expects cn/us/tw). "
                "which can lead to `Empty data from dataset` and missing portfolio artifacts. "
                "Set QLIB_FACTOR_BASE_CONFIG/QLIB_FACTOR_COMBINED_CONFIG to India templates when using in_data."
            )

        ret_df = pd.read_pickle(ret_path)
        logger.log_object(ret_df, tag="Quantitative Backtesting Chart")

        return pd.read_csv(csv_path, index_col=0).iloc[:, 0]
