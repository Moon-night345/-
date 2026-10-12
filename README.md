# 瓶安 BottleSafe

家庭化学品安全识别助手：上传产品照片后，输出产品信息、风险等级、储存建议、禁忌混用和暴露处置建议。

本仓库仅保留服务器部署所需的源码、配置、锁文件和运行时静态资源；参赛材料、训练数据、训练日志与模型权重均未包含。

## 目录

- `app/backend`：FastAPI 后端
- `app/frontend`：Next.js / vinext 前端
- `app/deploy`：Nginx 与 systemd 配置
- `app/studio`：Docker / ModelScope Studio 部署配置
- `scripts`：环境安装、模型下载与启动脚本

## API 模式快速启动

后端：

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt
export CHEM_BACKEND=api
export CHEM_API_KEY=你的密钥
export CHEM_API_BASE=https://api.siliconflow.cn/v1/chat/completions
export CHEM_API_MODEL=Qwen/Qwen3-VL-8B-Instruct
uvicorn src.web.app:app --host 0.0.0.0 --port 8001
```

前端：

```bash
cd app/frontend
npm ci
npm run build
npm run start
```

生产环境的 Nginx、systemd 与 GPU/CPU 部署说明见 `app/deploy/README.md`。

> 识别结果仅用于家庭风险筛查与安全教育，不能替代产品标签、SDS、医生或中毒控制中心的意见。

## License

MIT
