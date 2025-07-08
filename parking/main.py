# Copyright (c) 2024 Sungkyunkwan University AutomationLab
#
# Authors:
# - Gyuhyeon Hwang <rbgus7080@g.skku.edu>, Hobin Oh <hobin0676@daum.net>, Minkwan Choi <arbong97@naver.com>, Hyeonjin Sim <nufxwms@naver.com>
# - url: https://micro.skku.ac.kr/micro/index.do

from pynq import Overlay, MMIO, PL, allocate
from pynq.lib.video import *
from pynq_dpu import DpuOverlay
import cv2
import numpy as np
import time
import os
import spidev
import keyboard
import threading
from motor_controller import MotorController
from parking_system_controller import ParkingSystemController
from image_processor import ImageProcessor
from config import MOTOR_ADDRESSES, ULTRASONIC_ADDRESSES, ADDRESS_RANGE
from AutoLab_lib import init


def init_hardware():
    """하드웨어 초기화"""
    init()
    
    # SPI 초기화
    spi0 = spidev.SpiDev()
    spi0.open(0, 0)
    spi0.max_speed_hz = 20000000
    spi0.mode = 0b00
    
    return spi0


def init_motors():
    """모터 초기화"""
    motors = {}
    for name, addr in MOTOR_ADDRESSES.items():
        motors[name] = MMIO(addr, ADDRESS_RANGE)
    return motors


def init_ultrasonic_sensors():
    """초음파 센서 초기화"""
    ultrasonic_sensors = {}
    for name, addr in ULTRASONIC_ADDRESSES.items():
        ultrasonic_sensors[name] = MMIO(addr, ADDRESS_RANGE)
    return ultrasonic_sensors


def load_dpu():
    """DPU 로드 (선택사항 - 주차에서는 필요하지 않을 수 있음)"""
    try:
        overlay = DpuOverlay("../dpu/dpu.bit")
        overlay.load_model("../xmodel/top-tiny-yolov3_coco_256.xmodel")
        dpu = overlay.runner
        return overlay, dpu
    except Exception as e:
        print(f"DPU 로드 실패 (주차에서는 선택사항): {e}")
        return None, None


class ParkingMainController:
    """주차 메인 컨트롤러"""
    
    def __init__(self):
        # 하드웨어 초기화
        self.spi = init_hardware()
        
        # 모터 및 센서 초기화
        self.motors = init_motors()
        self.ultrasonic_sensors = init_ultrasonic_sensors()
        
        # 주차 설정
        self.parking_speed = 30      # 주차 속도 (0-100)
        self.steering_speed = 50     # 조향 속도 (0-100)
        
        # 컨트롤러 초기화
        self.motor_controller = MotorController(self.motors)
        self.motor_controller.init_motors()
        
        self.parking_controller = ParkingSystemController(
            self.motor_controller, 
            self.ultrasonic_sensors
        )
        
        # DPU 초기화 (선택사항)
        self.overlay, self.dpu = load_dpu()
        
        # 상태 변수
        self.is_running = False
        self.parking_active = False
        
        print("🚗 주차 시스템 초기화 완료")
    
    def start_parking(self):
        """주차 시작"""
        if not self.parking_active:
            self.parking_active = True
            self.parking_controller.start_parking()
            print("🚗 주차 시작!")
    
    def stop_parking(self):
        """주차 중지"""
        if self.parking_active:
            self.parking_active = False
            self.parking_controller.stop_parking()
            print("🛑 주차 중지!")
    
    def emergency_stop(self):
        """비상 정지"""
        self.parking_controller.emergency_stop()
        self.parking_active = False
        self.is_running = False
        print("🚨 비상 정지!")
    
    def reset_system(self):
        """시스템 리셋"""
        self.parking_controller.reset_system()
        self.parking_active = False
        print("🔄 시스템 리셋!")
    
    def parking_cycle_thread(self):
        """주차 사이클 실행 스레드"""
        while self.is_running:
            if self.parking_active:
                try:
                    # 센서 데이터 읽기
                    sensor_data = self.parking_controller.read_ultrasonic_sensors()
                    self.parking_controller.update_sensor_data(sensor_data)
                    
                    # 주차 사이클 실행
                    self.parking_controller.execute_parking_cycle()
                    
                    # 주차 완료 확인
                    if self.parking_controller.parking_completed:
                        print("🎉 주차 완료!")
                        self.parking_active = False
                        break
                    
                    time.sleep(0.1)  # 100ms 주기
                    
                except Exception as e:
                    print(f"❌ 주차 사이클 오류: {e}")
                    self.emergency_stop()
                    break
            else:
                time.sleep(0.1)
    
    def status_monitor_thread(self):
        """상태 모니터링 스레드"""
        while self.is_running:
            if self.parking_active:
                try:
                    status = self.parking_controller.get_status()
                    print(f"📊 단계: {status['phase']} - {status['status_message']}")
                    
                    # 센서 거리 출력
                    distances = status['sensor_distances']
                    print(f"   센서: FR={distances['front_right']:.1f}, "
                          f"ML={distances['middle_left']:.1f}, "
                          f"MR={distances['middle_right']:.1f}, "
                          f"RL={distances['rear_left']:.1f}, "
                          f"RR={distances['rear_right']:.1f}")
                    
                except Exception as e:
                    print(f"❌ 상태 모니터링 오류: {e}")
            
            time.sleep(1.0)  # 1초 주기
    
    def keyboard_input_thread(self):
        """키보드 입력 처리 스레드"""
        print("\n⌨️  키보드 조작:")
        print("  SPACE: 주차 시작/중지")
        print("  R: 시스템 리셋")
        print("  E: 비상 정지")
        print("  Q: 프로그램 종료")
        print("  C: 주차 설정 확인")
        print("  S: 센서 상태 확인")
        
        while self.is_running:
            try:
                if keyboard.is_pressed('space'):
                    if not self.parking_active:
                        self.start_parking()
                    else:
                        self.stop_parking()
                    time.sleep(0.5)  # 중복 입력 방지
                
                elif keyboard.is_pressed('r'):
                    self.reset_system()
                    time.sleep(0.5)
                
                elif keyboard.is_pressed('e'):
                    self.emergency_stop()
                    time.sleep(0.5)
                
                elif keyboard.is_pressed('q'):
                    print("👋 프로그램 종료...")
                    self.is_running = False
                    break
                
                elif keyboard.is_pressed('c'):
                    self.show_parking_config()
                    time.sleep(0.5)
                
                elif keyboard.is_pressed('s'):
                    self.show_sensor_status()
                    time.sleep(0.5)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ 키보드 입력 오류: {e}")
                time.sleep(0.1)
    
    def show_parking_config(self):
        """주차 설정 출력"""
        config = self.parking_controller.get_parking_config()
        print("\n⚙️  주차 설정:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    
    def show_sensor_status(self):
        """센서 상태 출력"""
        status = self.parking_controller.get_status()
        distances = status['sensor_distances']
        flags = status['sensor_flags']
        
        print("\n📡 센서 상태:")
        for sensor_name in distances.keys():
            detected = "✅" if flags.get(sensor_name, False) else "❌"
            print(f"  {sensor_name}: {distances[sensor_name]:.1f}cm {detected}")
    
    def run(self):
        """메인 실행 루프"""
        self.is_running = True
        
        try:
            # 스레드 시작
            parking_thread = threading.Thread(target=self.parking_cycle_thread, daemon=True)
            monitor_thread = threading.Thread(target=self.status_monitor_thread, daemon=True)
            keyboard_thread = threading.Thread(target=self.keyboard_input_thread, daemon=True)
            
            parking_thread.start()
            monitor_thread.start()
            keyboard_thread.start()
            
            print("🚗 주차 시스템 실행 중...")
            print("SPACE 키를 눌러 주차를 시작하세요.")
            
            # 메인 스레드에서 대기
            while self.is_running:
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단됨")
        except Exception as e:
            print(f"❌ 메인 실행 오류: {e}")
        finally:
            # 정리
            self.emergency_stop()
            if hasattr(self, 'motor_controller'):
                self.motor_controller.reset_motor_values()
            print("🔧 시스템 정리 완료")


def main():
    """메인 함수"""
    print("🚗 자율주차 시스템 시작")
    
    try:
        # 주차 메인 컨트롤러 생성 및 실행
        controller = ParkingMainController()
        controller.run()
        
    except Exception as e:
        print(f"❌ 시스템 초기화 오류: {e}")
        print("하드웨어 연결을 확인해주세요.")


if __name__ == "__main__":
    main()