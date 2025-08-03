import cv2
img = cv2.imread("uav_simulator/ceshi.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
colored = cv2.applyColorMap(gray, cv2.COLORMAP_JET)  # 模拟红外热图
cv2.imwrite("fake_ir.jpg", colored)