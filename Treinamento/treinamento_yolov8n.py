from ultralytics import YOLO
import os


arquivo_config = 'configs/configs_modelo.yaml'

model = YOLO('yolov8s.yaml')

resultados = model.train(
    data=arquivo_config, 
    epochs=140, 
    imgsz=640, 
    name='yolov8s_modelo')

dir_resultado = os.path.join('runs', 'detect', 'yolov8s_modelo')
print(f"Resultados salvos em: {dir_resultado}")


