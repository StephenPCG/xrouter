# 其他记录

在高分辨率屏幕上，console 的字体非常小，可以这样操作：

修改 `/etc/default/grub`：
```
# 如果这个变量有值，则增加一个 nomodeset
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset"
```

然后 `sudo update-grub` 即可。
