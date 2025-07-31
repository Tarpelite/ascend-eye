默认四个视频流同时推送，端口为5000,5001,5002,5003
也可以使用参数自行定义:
只需提供文件名，自动去文件夹下找文件，需要在test_videos和label_video两个文件夹下都有该文件
python run_simulator.py --videos test.mp4 test.mp4 test.mp4 test.mp4 --ports 5000 5001 5002 5003