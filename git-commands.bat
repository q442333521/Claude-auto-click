@echo off
REM 设置Git用户信息（如果尚未设置）
git config --global user.email "442333521@qq.com"
git config --global user.name "wzy"

REM 添加所有修改的文件
git add .

REM 提交更改
git commit -m "改用PyAutoGUI进行图像识别，提高匹配成功率"

REM 如果需要，可以设置/更新远程仓库
git remote remove origin
git remote add origin https://6662228.xyz:10024/wzy/Claude-auto-click.git

REM 推送到远程仓库
git push -u origin main

REM 完成后暂停
echo.
echo 提交完成! 请检查上面的输出信息。
pause
