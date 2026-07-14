# 打样中心模具参数库（Python / Streamlit）

用于记录模具基本信息、射出与保压、开关模、托模、油管使用以及图文备注。

## 本机运行

电脑需要先安装 Python 3.10 或更高版本。

### Windows 一键启动

双击 `启动系统.bat`。首次运行会安装 Streamlit 和 pandas，耗时可能为数分钟。浏览器通常会自动打开：

<http://localhost:8501>

### 命令行启动

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

本机数据保存在同目录的 `molds.db`。该文件已被 `.gitignore` 排除，不会上传到 GitHub。请同时使用系统左侧的“导出全部备份”。

## GitHub + Streamlit Community Cloud 部署

1. 在 GitHub 新建一个公开仓库，例如 `mold-parameter-system`。
2. 把本目录全部文件上传到仓库，注意 `.streamlit/config.toml` 也要上传。
3. 打开 <https://share.streamlit.io/>，使用 GitHub 登录。
4. 点击 **Create app**，选择刚才的仓库和 `main` 分支。
5. Main file path 填写 `app.py`，点击 **Deploy**。
6. 等待构建完成，即可获得可分享的网址。

## 重要说明

Streamlit Community Cloud 免费环境的本地磁盘不是永久数据库，应用休眠、重启或重新部署后，云端新录入的数据可能丢失。因此：

- 试用阶段请经常导出 JSON 备份；
- 正式多人使用时，建议接入 Supabase、PostgreSQL 等云数据库；
- 模具参数属于生产资料，公开仓库只应放程序代码，不应放真实模具数据库和现场照片。
