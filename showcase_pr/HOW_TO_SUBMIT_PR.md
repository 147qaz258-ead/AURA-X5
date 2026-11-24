# 双 GitHub 仓库提交实操指南（Warehouse A + Warehouse B）

地瓜冬季挑战赛规定代码与参赛展示文档分离，需要操作**两个不同的 GitHub 仓库**：

1. **仓库 A（你自己的公开项目仓库）**：放完整源码、ROS 2 包、KiCad PCB/Gerber、CadQuery 3D 文件、技术文档、测试脚本、截图证据与 `LICENSE`（就是你本地整个 `aura_x5/` 文件夹）。
2. **仓库 B（地瓜官方赛事仓库的 Fork）**：`D-Robotics/Robotics-Dream-Keeper-Challenge-Winter`。**不要往这里传源码或大视频**，只通过 Pull Request 往它的 `projects/` 目录下提交**一份 Markdown 展示文件**：
   `projects/<ParticipantName>-Project-AURA-X5.md`。

---

## 第一步：发布「仓库 A」（你自己的公开项目仓库）

1. 登录 GitHub，点击右上角 **New repository**，仓库名填 `AURA-X5`，可见性选 **Public**，不要勾选自带 README/License（本地都已生成好）。
2. 在本地 `aura_x5/` 目录初始化并推送：

```powershell
cd E:\C_Projects\地瓜dot比赛\aura_x5
git init -b main
git add .
git commit -m "feat: AURA-X5 RDK X5 embodied proactive AI co-pilot (Stage 1-2 + ROS 2)"
git remote add origin https://github.com/<你的GitHub用户名>/AURA-X5.git
git push -u origin main
```

3. 推送前安全检查：确认 `git status` 中没有 `.env`、私钥、密码或超大原始视频（`.gitignore` 已屏蔽，单元测试 `test_no_hardcoded_ssh_passwords_in_scripts` 已验证脚本无硬编码密码）。

---

## 第二步：提交「仓库 B」（向官方赛事仓库发 Showcase Pull Request）

1. 打开官方仓库页面：`https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter`
2. 点击右上角 **Fork**，把它复刻到你的 GitHub 账号下。
3. 在一个**独立目录**（不要嵌套在 `aura_x5/` 里）克隆你的 Fork 并建提交分支：

```powershell
cd E:\C_Projects
git clone https://github.com/<你的GitHub用户名>/Robotics-Dream-Keeper-Challenge-Winter.git
cd Robotics-Dream-Keeper-Challenge-Winter
git remote add upstream https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter.git
git switch -c showcase/<你的英文名>-stage2
```

4. 把我已按官方模板写好的草案复制到官方仓库的 `projects/` 目录下并重命名（`<ParticipantName>` 换成你的参赛英文名，无空格、无 `-v2` 后缀）：

```powershell
Copy-Item E:\C_Projects\地瓜dot比赛\aura_x5\showcase_pr\ParticipantName-Project-AURA-X5.md .\projects\<你的英文名>-Project-AURA-X5.md
```

5. 编辑 `projects/<你的英文名>-Project-AURA-X5.md`，把里面的 `<YourParticipantName>`、`<YOUR_GITHUB_USERNAME>`、`<YOUR_PUBLIC_DEMO_VIDEO_URL>`、`<YOUR_DISCORD_THREAD_PERMALINK>` 替换成真实公开链接，并删除顶部提示注释。
6. 提交并推送到你的 Fork：

```powershell
git add projects/<你的英文名>-Project-AURA-X5.md
git commit -m "Add showcase: <你的英文名> AURA-X5"
git push -u origin showcase/<你的英文名>-stage2
```

7. 打开 GitHub，向 `D-Robotics/Robotics-Dream-Keeper-Challenge-Winter` 的默认分支发起 **Pull Request**：
   - **PR 标题**：`[Showcase] <你的英文名> — AURA-X5 (Stage 2)`
   - **PR 描述勾选清单**（官方必填）：
     ```markdown
     - [x] Participant name matches the filename
     - [x] Current stage is stated
     - [x] Source repository is public
     - [x] Required evidence links are included
     - [x] Demo link is stable
     - [x] I agree that this showcase document may be used for program promotion, judging, and archives
     ```

8. **后续推进到 Stage 3 时**：不需要新建第二个文件！直接修改同一份 `projects/<你的英文名>-Project-AURA-X5.md`（把 `Stage completed` 改成 `3`，补上最终 1080P 视频链接和 BPU 实测表链接），再提交 PR 更新即可。
