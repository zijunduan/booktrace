# BookTrace 书痕

BookTrace 是一个 Windows 本地读书感想捕捉器。它常驻系统托盘，按 `Ctrl+Alt+N` 呼出小窗口，写下“书名 + 感想”，并自动按书保存为 Markdown。

## 功能

- `Ctrl+Alt+N`：随时打开记录窗口
- `Ctrl+Alt+B`：打开书架
- `Ctrl+Alt+R`：随机回忆
- `Ctrl+Alt+O`：打开当前书痕
- 自动保存到 `data/notes/书名.md`
- 书架窗口按卡片回看每本书的感想
- 随机回忆：从旧笔记里随机捞一句
- 可选择一个已有文件夹作为笔记目录

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 运行

```powershell
python main.py
```

启动后默认只显示系统托盘图标。右键托盘图标可以选择“记一念”“打开书架”“随机回忆”“打开笔记文件夹”“选择笔记文件夹”或“退出”。

## 记录窗口快捷键

- `Ctrl+Enter`：保存
- `Esc`：隐藏窗口
- `Ctrl+L`：聚焦并全选书名
- `Ctrl+K`：清空感想

## 保存格式

每本书一个 Markdown 文件：

```markdown
# 雪国

## 2026-06-19

- 12:45 像是把现实冻成了一个梦。
```

同一天保存多条感想时，只会保留一个日期标题。

## 笔记文件夹

默认笔记目录是：

```text
data/notes/
```

配置文件位于：

```text
data/config.json
```

其中 `notes_dir` 表示笔记目录，`last_book` 表示上次记录的书名。你可以直接编辑 `notes_dir`，也可以从托盘菜单点击“选择笔记文件夹”，把已有 Markdown 笔记文件夹导入 BookTrace 的书架视图。

## 打包 exe

先安装 PyInstaller：

```powershell
pip install pyinstaller
```

推荐先使用文件夹模式：

```powershell
pyinstaller -w main.py --name BookTrace --add-data "ui/style.qss;ui"
```

如果需要单文件：

```powershell
pyinstaller -F -w main.py --name BookTrace --add-data "ui/style.qss;ui"
```

打包后，`config.json` 和笔记仍会保存在 exe 同级目录下的 `data/` 文件夹中。

## 当前边界

BookTrace 保持克制：只做快捷记录、按书保存、卡片回看和随机重逢，不加入标签、评分、封面、阅读进度或 AI 总结。
