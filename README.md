# MCR Arena: 3D Wave Survival Shooter

這是一個使用 Python 與 **Ursina Engine** 開發的 3D 第一人稱射擊生存遊戲。玩家必須在無盡的敵人波次中生存，收集物資並挑戰最高分。

## 🎮 遊戲特色 (Features)
* **波次系統**：難度隨波次增加，敵人數量會越來越多。
* **多樣化敵人**：
    * **基本敵人**：近距離追蹤攻擊。
    * **狙擊手 (Sniper)**：具備遠程射擊能力與預警機制。
* **戰鬥系統**：
    * 真實的彈道與彈殼拋射效果。
    * 手榴彈投擲與範圍爆炸傷害。
* **物資補給 (Loot)**：擊殺敵人有機率掉落生命值、彈藥或手榴彈補給。
* **UI 介面**：包含生命/彈藥顯示、受傷紅屏特效、小地圖 (Minimap) 系統。
* **紀錄保存**：自動儲存最高分 (High Score)。

## 🛠 安裝與執行 (Installation)

1. **Clone 專案**
   ```bash
   git clone [https://github.com/您的帳號/mcr-arena.git](https://github.com/您的帳號/mcr-arena.git)
   cd mcr-arena

本遊戲需要安裝 ursina 引擎。請執行以下指令自動安裝所需套件：

   pip install -r requirements.txt
   
執行主程式檔案：

  python 666666.PY
---------------------
系統需求

Python 3.6+

支援 OpenGL 的顯示卡 (Ursina 需求)
-----------------------
操作說明 (Controls)

按鍵,功能
"W, A, S, D",移動 (Move)

滑鼠左鍵,射擊 (Shoot)

R,重新裝填 (Reload)

G,投擲手榴彈 (Throw Grenade)

ESC,暫停/選單 (Pause/Menu)
