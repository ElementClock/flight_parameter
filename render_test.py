#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import wx
import wx.html as html

class RenderTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="HTML渲染测试")
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建HTML窗口
        self.html_window = html.HtmlWindow(panel)
        sizer.Add(self.html_window, 1, wx.EXPAND | wx.ALL, 5)
        
        # 测试HTML内容
        test_html = '''<html>
<body style="font-family: Consolas, 'Courier New', monospace;">
<div style="display: block; margin: 1em 0; text-align: center; font-weight: bold;">
动力分析结果
</div>
<table border="1" cellspacing="0" cellpadding="3">
<tr>
<th>列1</th>
<th>列2</th>
<th>列3</th>
</tr>
<tr>
<td>数据1</td>
<td>数据2</td>
<td>数据3</td>
</tr>
<tr>
<td>数据4</td>
<td>数据5</td>
<td>数据6</td>
</tr>
</table>
</body>
</html>'''
        
        # 设置HTML内容
        self.html_window.SetPage(test_html)
        
        panel.SetSizer(sizer)
        self.SetSize((600, 400))

class RenderTestApp(wx.App):
    def OnInit(self):
        frame = RenderTestFrame()
        frame.Show()
        return True

if __name__ == '__main__':
    app = RenderTestApp()
    app.MainLoop()