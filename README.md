# MCR Arena: 3D Wave Survival Shooter

這是一個使用 Python 與 **Ursina Engine** 開發的 3D 第一人稱射擊生存遊戲 (FPS)。玩家必須在無盡的敵人波次中生存，利用戰術手榴彈、狙擊與走位來挑戰最高分。

## 🎮 遊戲特色 (Features)

* **無盡波次系統 (Infinite Waves)**：難度隨波次增加，敵人數量與強度會逐漸提升。
* **多樣化敵人 AI**：
    * **追蹤者 (Enemy)**：快速接近並進行近身攻擊。
    * **狙擊手 (Sniper)**：具備遠程射擊能力、預警雷射與冷卻機制。
* **戰鬥系統**：
    * 真實的彈道軌跡 (Bullet Trails) 與彈殼拋射效果。
    * 手榴彈投擲 (物理碰撞與範圍爆炸傷害)。
    * 受傷紅屏特效與動態準心。
* **物資補給 (Loot System)**：擊殺敵人有機率掉落生命值、彈藥或手榴彈補給包。
* **HUD 戰術介面**：包含生命/彈藥顯示、雷達小地圖 (Minimap) 系統。
* **紀錄保存**：自動儲存並讀取本地最高分 (High Score)。

## 🛠 安裝與執行 (Installation)

請依照以下步驟在您的電腦上安裝並執行遊戲：

### 1. 下載專案 (Clone Repository)
開啟終端機 (Terminal/CMD)，執行以下指令將專案下載至本地：
```bash
git clone [https://github.com/kenshinsanli/congenial-enigma.git](https://github.com/kenshinsanli/congenial-enigma.git)
cd congenial-enigma



---------------------
本遊戲需要安裝 ursina 引擎。請執行以下指令自動安裝所需套件：

   pip install -r requirements.txt
---------------------   
執行主程式檔案：

  python 666666.PY
---------------------
系統需求 (Requirements)

OS: Windows, macOS, or Linux

Python: Python 3.6 或以上版本

Graphics: 支援 OpenGL 的顯示卡 (Ursina 引擎需求)
-----------------------
操作說明 (Controls)

按鍵,功能
"W, A, S, D",移動 (Move)

滑鼠左鍵,射擊 (Shoot)

R,重新裝填 (Reload)

G,投擲手榴彈 (Throw Grenade)

ESC,暫停/選單 (Pause/Menu)
