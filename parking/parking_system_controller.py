import pygame
import math
import random
import time

# Pygame 초기화
pygame.init()

# 화면 설정
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("차량 주차 시뮬레이션")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# 한글 폰트 설정
def get_korean_font(size):
    """한글 폰트 가져오기"""
    import platform
    import os
    
    try:
        system = platform.system()
        
        if system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                "/Library/Fonts/AppleSDGothicNeo.ttc",
                "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
                "/Library/Fonts/Arial Unicode.ttf"
            ]
        elif system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/malgun.ttf",  # 맑은 고딕
                "C:/Windows/Fonts/gulim.ttc",   # 굴림
                "C:/Windows/Fonts/batang.ttc",  # 바탕
                "C:/Windows/Fonts/NanumGothic.ttf",  # 나눔고딕
                "C:/Windows/Fonts/NanumBarunGothic.ttf"  # 나눔바른고딕
            ]
        else:  # Linux
            font_paths = [
                # 한글 폰트를 우선적으로 확인
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
                "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
                "/usr/share/fonts/truetype/fonts-nanum/NanumGothic.ttf",
                "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf",
                "/usr/share/fonts/truetype/unfonts-core/UnBatang.ttf",
                "/usr/share/fonts/truetype/baekmuk/dotum.ttf",
                "/usr/share/fonts/truetype/baekmuk/batang.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
                # 구글 폰트
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                # 우분투 한글 폰트
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
                # Liberation은 한글 지원 안함 - 제거
            ]
        
        # 폰트 파일 찾기
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"폰트 확인 중: {font_path}")
                try:
                    test_font = pygame.font.Font(font_path, size)
                    # 한글 렌더링 테스트
                    test_render = test_font.render("한글", True, (0, 0, 0))
                    if test_render.get_width() > 0:  # 렌더링 성공
                        print(f"한글 폰트 로드 성공: {font_path}")
                        return test_font
                except:
                    continue
        
        # 시스템에 설치된 폰트 확인
        print("\n시스템 폰트에서 한글 폰트 검색 중...")
        import subprocess
        try:
            # fc-list 명령으로 한글 폰트 찾기
            result = subprocess.run(['fc-list', ':lang=ko'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '.ttf' in line or '.otf' in line:
                        font_path = line.split(':')[0].strip()
                        if os.path.exists(font_path):
                            try:
                                test_font = pygame.font.Font(font_path, size)
                                print(f"한글 폰트 발견: {font_path}")
                                return test_font
                            except:
                                continue
        except:
            pass
        
        # 폰트를 찾지 못한 경우
        print("\n한글 폰트를 찾을 수 없습니다. 다음 명령으로 설치해주세요:")
        print("sudo apt-get install fonts-nanum fonts-unfonts-core")
        
        # 기본 폰트 사용
        return pygame.font.Font(None, size)
        
    except Exception as e:
        print(f"폰트 로드 실패: {e}")
        # 기본 폰트 사용
        return pygame.font.Font(None, size)

# 폰트 설정
font = get_korean_font(20)
big_font = get_korean_font(32)

class Vehicle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = -90  # 차량 각도 (도) - 위쪽을 향하도록
        self.width = 60
        self.height = 30
        self.speed = 0
        self.steering_angle = 0
        
        # 센서 위치 (차량 중심 기준 상대 좌표)
        # 차량이 위를 향할 때 기준
        # x: 양수는 전방, 음수는 후방
        # y: 양수는 우측, 음수는 좌측
        self.sensor_positions = {
            "front_right": (15, 15),    # 전방 우측
            "middle_left": (0, -15),    # 중간 좌측
            "middle_right": (0, 15),    # 중간 우측
            "rear_left": (-15, -15),    # 후방 좌측
            "rear_right": (-15, 15)     # 후방 우측
        }
        
        # 센서 거리값
        self.sensor_distances = {
            "front_right": 100,
            "middle_left": 100,
            "middle_right": 100,
            "rear_left": 100,
            "rear_right": 100
        }
        
        # 이전 거리값 (정지 감지용)
        self.previous_distances = {
            "front_right": -1,
            "middle_right": -1,
            "rear_right": -1
        }
        
        # 각 센서별 감지 상태 플래그
        self.sensor_flags = {
            "front_right": False,  # 작아졌다가 커진 적이 있는지
            "middle_right": False,
            "rear_right": False
        }
        
        # 상태 변수
        self.stop_detected = False
        self.initial_forward_started = False  # 초기 전진 시작 여부 추가
        self.first_stop_completed = False
        self.left_turn_started = False
        self.second_stop_completed = False
        self.right_turn_started = False
        self.backward_completed = False
        self.alignment_completed = False  # 7단계 정렬 완료 여부 추가
        self.straight_backward_started = False  # 정방향 후진 시작 여부 추가
        self.correction_started = False  # 10단계 수정 시작 여부 추가
        self.left_correction_started = False  # 좌측 치우침 수정 시작 여부 추가
        self.right_correction_started = False  # 우측 치우침 수정 시작 여부 추가
        self.correction_start_time = None  # 수정 시작 시간 추가
        self.rear_right_previous = -1
        self.backward_start_time = None  # 후진 시작 시간 추가
        self.straight_backward_start_time = None  # 정방향 후진 시작 시간 추가
        self.correction_completed = False  # 수정 완료 여부 추가
        self.post_correction_backward_started = False  # 수정 후 정방향 후진 시작 여부 추가
        self.post_correction_backward_start_time = None  # 수정 후 정방향 후진 시작 시간 추가
        self.additional_backward_start_time = None  # 추가 후진 시작 시간 추가
        self.parking_completion_forward_started = False  # 주차 완료 후 정방향 직진 시작 여부 추가
        self.parking_completion_forward_start_time = None  # 주차 완료 후 정방향 직진 시작 시간 추가
        self.rear_right_sudden_increase_detected = False  # rear_right 갑작스러운 증가 감지 여부 추가
        self.rear_right_previous_for_forward = -1  # 정방향 직진 중 rear_right 이전 값 추가
        self.right_turn_after_increase_started = False  # 증가 후 오른쪽 조향 시작 여부 추가
        self.right_turn_after_increase_start_time = None  # 증가 후 오른쪽 조향 시작 시간 추가
        self.parking_completion_stop_started = False  # 주차 완료 후 정지 시작 여부 추가
        self.parking_completion_stop_start_time = None  # 주차 완료 후 정지 시작 시간 추가
        
        # 상태 메시지
        self.status_message = "대기 중..."
        self.phase = 0  # 현재 단계 - 0부터 시작
    
    def update_sensors(self, obstacles):
        """센서 거리 업데이트"""
        for sensor_name, rel_pos in self.sensor_positions.items():
            # 센서의 절대 위치 계산
            angle_rad = math.radians(self.angle)
            sensor_x = self.x + rel_pos[0] * math.cos(angle_rad) - rel_pos[1] * math.sin(angle_rad)
            sensor_y = self.y + rel_pos[0] * math.sin(angle_rad) + rel_pos[1] * math.cos(angle_rad)
            
            # 센서 방향 (차량이 위를 향할 때 기준)
            if "right" in sensor_name:
                sensor_angle = self.angle + 90  # 우측 센서는 오른쪽을 향함
            else:
                sensor_angle = self.angle - 90  # 좌측 센서는 왼쪽을 향함
            
            # 레이캐스팅으로 거리 측정
            min_distance = 400  # 최대 거리
            for obstacle in obstacles:
                dist = self.ray_cast_to_obstacle(sensor_x, sensor_y, sensor_angle, obstacle)
                if dist < min_distance:
                    min_distance = dist
            
            self.sensor_distances[sensor_name] = min_distance
    
    def ray_cast_to_obstacle(self, x, y, angle, obstacle):
        """레이캐스팅으로 장애물까지의 거리 계산"""
        angle_rad = math.radians(angle)
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)
        
        # 레이를 따라 이동하며 장애물과의 충돌 검사
        for i in range(400):
            check_x = x + i * dx
            check_y = y + i * dy
            
            # 장애물과 충돌 검사
            if (obstacle.x <= check_x <= obstacle.x + obstacle.width and
                obstacle.y <= check_y <= obstacle.y + obstacle.height):
                return i
        
        return 400  # 최대 거리
    
    def check_stop_condition(self):
        """첫 번째 정지 조건 확인"""
        current_distances = {
            "front_right": self.sensor_distances["front_right"],
            "middle_right": self.sensor_distances["middle_right"],
            "rear_right": self.sensor_distances["rear_right"]
        }
        
        # 각 센서별로 개별적으로 작아졌다가 커지는지 확인
        for sensor_name in ["front_right", "middle_right", "rear_right"]:
            current = current_distances[sensor_name]
            previous = self.previous_distances[sensor_name]
            
            # 아직 감지되지 않은 센서만 확인
            if not self.sensor_flags[sensor_name] and previous > 0:
                if current > previous + 5:  # 5cm 이상 증가
                    self.sensor_flags[sensor_name] = True
                    print(f"✅ {sensor_name} 센서 감지 완료!")
        
        # 모든 우측 센서가 한 번씩 작아졌다가 커졌는지 확인
        if all(self.sensor_flags.values()) and not self.first_stop_completed:
            self.stop_detected = True
            self.status_message = "모든 우측 센서 감지 완료! 정지 신호!"
            return True
        
        self.previous_distances = current_distances.copy()
        return False
    
    def check_second_stop_condition(self):
        """두 번째 정지 조건 확인"""
        rear_right_current = self.sensor_distances["rear_right"]
        
        if rear_right_current > 0 and self.rear_right_previous > 0:
            if rear_right_current > self.rear_right_previous + 10:
                self.status_message = "두 번째 정지 신호 감지!"
                return True
        
        self.rear_right_previous = rear_right_current
        return False
    
    def check_backward_completion(self):
        """후진 완료 조건 확인"""
        front_right_distance = self.sensor_distances["front_right"]
        
        if front_right_distance <= 40:  # 20cm 이하
            self.status_message = "후진 완료!"
            return True
        
        return False
    
    def check_alignment_completion(self):
        """차량 정렬 완료 조건 확인"""
        front_right_distance = self.sensor_distances["front_right"]
        rear_right_distance = self.sensor_distances["rear_right"]
        
        # 센서 값이 유효한지 확인 (0보다 큰 값)
        if front_right_distance <= 0 or rear_right_distance <= 0:
            return False
        
        # front_right와 rear_right 값의 차이 계산
        distance_diff = front_right_distance - rear_right_distance
        tolerance = 0.0  # 허용 오차 (3cm)
        
        # 차량 정렬 상태 확인
        if abs(distance_diff) <= tolerance:
            # 두 센서 값이 거의 같으면 정렬 완료
            self.status_message = "차량 정렬 완료! 주차 완료!"
            return True
        else:
            # 차량 정렬을 위한 조향 조정
            if distance_diff > 0:
                # front_right가 더 크면 왼쪽으로 조향
                self.steering_angle = -5
                self.status_message = "왼쪽 조향으로 정렬 중..."
            else:
                # rear_right가 더 크면 오른쪽으로 조향
                self.steering_angle = 5
                self.status_message = "오른쪽 조향으로 정렬 중..."
            
            return False
    
    def stop_vehicle(self):
        """차량 정지"""
        self.speed = 0
        self.steering_angle = 0
        self.first_stop_completed = True
        self.phase = 2
        self.status_message = "첫 번째 정지 완료"
    
    def start_left_turn_and_forward(self):
        """왼쪽 조향 후 전진"""
        self.left_turn_started = True
        self.steering_angle = -20  # 왼쪽으로 20도 (차량이 위를 향하고 있으므로 음수)
        self.speed = 2  # 전진
        self.phase = 3
        self.status_message = "왼쪽 조향 전진 중..."
    
    def stop_vehicle_second(self):
        """두 번째 정지"""
        self.speed = 0
        self.steering_angle = 0
        self.second_stop_completed = True
        self.phase = 4
        self.status_message = "두 번째 정지 완료"
    
    def start_right_turn_and_backward(self):
        """오른쪽 조향 후 후진"""
        self.right_turn_started = True
        self.steering_angle = 13  # 오른쪽으로 13도 (차량이 위를 향하고 있으므로 양수)
        self.speed = -1  # 후진 속도를 -2에서 -1로 낮춤
        self.phase = 5
        self.status_message = "오른쪽 조향 후진 중..."
        self.backward_start_time = time.time()  # 후진 시작 시간 기록
    
    def stop_backward(self):
        """후진 정지 (6단계 완료) - 정방향 후진 시작"""
        self.speed = -1  # 정방향 후진 계속
        self.steering_angle = 0  # 조향각 0으로 설정 (정방향)
        self.backward_completed = True
        self.straight_backward_started = True
        self.straight_backward_start_time = time.time()  # 정방향 후진 시작 시간 기록
        self.phase = 6
        self.status_message = "후진 완료! 정방향 후진 중..."
    
    def check_straight_backward_completion(self):
        """정방향 후진 완료 조건 확인"""
        if self.straight_backward_start_time is None:
            return False
        
        elapsed_time = time.time() - self.straight_backward_start_time
        straight_backward_duration = 0.3  # 1.5초 동안 정방향 후진
        
        if elapsed_time >= straight_backward_duration:
            self.status_message = "정방향 후진 완료! 정렬 시작..."
            return True
        
        return False
    
    def complete_straight_backward(self):
        """정방향 후진 완료"""
        self.speed = 0
        self.steering_angle = 0
        self.straight_backward_started = False
        self.phase = 7
        self.status_message = "정방향 후진 완료! 정렬 시작..."
    
    def start_alignment(self):
        """8단계: 차량 정렬 시작"""
        self.speed = -1  # 느린 후진으로 정렬
        self.phase = 8
        self.status_message = "차량 정렬 중..."
    
    def complete_alignment(self):
        """8단계: 정렬 완료"""
        self.speed = 0
        self.steering_angle = 0
        self.alignment_completed = True
        self.phase = 9
        self.status_message = "주차 완료! 위치 확인 중..."
    
    def check_position_correction_needed(self):
        """9단계: 위치 수정 필요 여부 확인"""
        middle_right_distance = self.sensor_distances["middle_right"]
        middle_left_distance = self.sensor_distances["middle_left"]
        
        # 센서 값이 유효한지 확인 (둘 다 0 이하일 때만 무시)
        if middle_right_distance <= 0 and middle_left_distance <= 0:
            self.status_message = "주차 완료!"
            return False
        
        # middle_right와 middle_left 값의 차이 계산
        distance_diff = abs(middle_right_distance - middle_left_distance)
        correction_threshold = 10  # 10cm 이상 차이나면 수정 필요
        
        if distance_diff >= correction_threshold:
            # 수정이 필요한 경우
            if middle_right_distance > middle_left_distance:
                self.status_message = "좌측으로 치우침! 수정 필요!"
            else:
                self.status_message = "우측으로 치우침! 수정 필요!"
            return True
        else:
            # 수정이 필요하지 않은 경우
            self.status_message = "주차 완료!"
            return False
    
    def start_correction(self):
        """10단계: 위치 수정 시작"""
        self.correction_started = True
        self.correction_start_time = time.time()  # 수정 시작 시간 기록
        self.phase = 10
        
        # 현재 상태 메시지에 따라 수정 방향 결정
        if "좌측으로 치우침" in self.status_message:
            self.left_correction_started = True
            self.speed = 1  # 전진
            self.steering_angle = 15  # 오른쪽으로 15도 조향
            self.status_message = "좌측 치우침 수정 중... (우회전 후 좌회전)"
        elif "우측으로 치우침" in self.status_message:
            self.right_correction_started = True
            self.speed = 1  # 전진
            self.steering_angle = -15  # 왼쪽으로 15도 조향
            self.status_message = "우측 치우침 수정 중... (좌회전 후 우회전)"
        # 메시지는 check_position_correction_needed에서 설정된 것을 유지
        # self.status_message = "위치 수정 중... (로직 미구현)"
    
    def check_left_correction_completion(self):
        """좌측 치우침 수정 완료 조건 확인"""
        if not self.left_correction_started or self.correction_start_time is None:
            return False
        
        elapsed_time = time.time() - self.correction_start_time
        
        # 1단계: 점진적으로 왼쪽으로 조향 (1초에 걸쳐 15도에서 -15도로)
        if elapsed_time < 2.0:
            # 1초에 걸쳐 10도에서 -10도로 (총 15도 변화)
            steering_reduction = (elapsed_time / 2.0) * 30
            self.steering_angle = 15 - steering_reduction
            return False
        
        # 2단계: 완료
        else:
            self.speed = 0
            self.steering_angle = 0
            self.status_message = "좌측 치우침 수정 완료!"
            return True
    
    def check_right_correction_completion(self):
        """우측 치우침 수정 완료 조건 확인"""
        if not self.right_correction_started or self.correction_start_time is None:
            return False
        
        elapsed_time = time.time() - self.correction_start_time
        
        # 1단계: 점진적으로 오른쪽으로 조향 (2초에 걸쳐 -20도에서 20도로)
        if elapsed_time < 2.0:
            # 2초에 걸쳐 -20도에서 20도로 (총 40도 변화)
            steering_increase = (elapsed_time / 2.0) * 30
            self.steering_angle = -15 + steering_increase
            return False
        
        # 2단계: 완료
        else:
            self.speed = 0
            self.steering_angle = 0
            self.status_message = "우측 치우침 수정 완료!"
            return True
    
    def complete_correction(self):
        """10단계: 위치 수정 완료"""
        self.speed = 0
        self.steering_angle = 0
        self.correction_started = False
        self.correction_completed = True
        self.phase = 11
        self.status_message = "수정 완료! 정방향 후진 시작..."
    
    def start_post_correction_backward(self):
        """11단계: 수정 후 정방향 후진 시작"""
        self.post_correction_backward_started = True
        self.post_correction_backward_start_time = time.time()
        self.speed = -1  # 후진
        self.steering_angle = 0  # 정방향
        self.phase = 11
        self.status_message = "수정 후 정방향 후진 중..."
    
    def check_post_correction_backward_completion(self):
        """수정 후 정방향 후진 완료 조건 확인"""
        if self.post_correction_backward_start_time is None:
            return False
        
        # front_right 센서 거리 확인
        front_right_distance = self.sensor_distances["front_right"]
        
        # front_right가 40 이하가 되면 추가 후진 시작 시간 기록
        if front_right_distance <= 40 and self.additional_backward_start_time is None:
            self.additional_backward_start_time = time.time()
            self.status_message = "front_right 40cm 이하! 추가 정방향 후진 시작..."
        
        # 추가 후진 시작 후 1.5초가 지나면 완료
        if self.additional_backward_start_time is not None:
            elapsed_time = time.time() - self.additional_backward_start_time
            if elapsed_time >= 0.5:
                self.status_message = "수정 후 정방향 후진 완료!"
                return True
        
        return False
    
    def complete_post_correction_backward(self):
        """수정 후 정방향 후진 완료"""
        self.speed = 0
        self.steering_angle = 0
        self.post_correction_backward_started = False
        self.phase = 12
        self.status_message = "최종 주차 완료! 2초 정지 시작..."
        # 주차 완료 후 2초 정지 시작
        self.start_parking_completion_stop()
    
    def start_parking_completion_forward(self):
        """13단계: 주차 완료 후 정방향 직진 시작"""
        self.parking_completion_forward_started = True
        self.parking_completion_forward_start_time = time.time()
        self.speed = 2  # 전진
        self.steering_angle = 0  # 정방향
        self.phase = 13
        self.status_message = "주차 완료! 정방향 직진 중..."
    
    def check_rear_right_sudden_increase(self):
        """rear_right 값의 갑작스러운 증가 감지"""
        if not self.parking_completion_forward_started:
            return False
        
        current_rear_right = self.sensor_distances["rear_right"]
        
        # 이전 값이 유효하고 현재 값이 갑자기 커졌는지 확인
        if self.rear_right_previous_for_forward > 0 and current_rear_right > 0:
            if current_rear_right > self.rear_right_previous_for_forward + 15:  # 15cm 이상 증가
                self.rear_right_sudden_increase_detected = True
                self.status_message = "rear_right 갑작스러운 증가 감지! 오른쪽 조향 시작..."
                return True
        
        self.rear_right_previous_for_forward = current_rear_right
        return False
    
    def start_right_turn_after_increase(self):
        """rear_right 증가 후 오른쪽 조향 시작"""
        self.right_turn_after_increase_started = True
        self.right_turn_after_increase_start_time = time.time()
        self.speed = 2  # 전진 유지
        self.steering_angle = 20  # 오른쪽으로 20도 조향
        self.status_message = "오른쪽 20도 조향 중..."
    
    def check_right_turn_completion(self):
        """오른쪽 조향 완료 조건 확인"""
        if not self.right_turn_after_increase_started or self.right_turn_after_increase_start_time is None:
            return False
        
        elapsed_time = time.time() - self.right_turn_after_increase_start_time
        turn_duration = 1.5  # 0.5초 동안 오른쪽 조향
        
        if elapsed_time >= turn_duration:
            self.speed = 0
            self.steering_angle = 0
            self.status_message = "오른쪽 조향 완료! 정방향 주행 시작..."
            return True
        
        return False
    
    def start_final_forward(self):
        """14단계: 최종 정방향 주행 시작"""
        self.speed = 2  # 전진
        self.steering_angle = 0  # 정방향
        self.phase = 14
        self.status_message = "최종 정방향 주행 중..."
    
    def start_parking_completion_stop(self):
        """주차 완료 후 2초 정지 시작"""
        self.parking_completion_stop_started = True
        self.parking_completion_stop_start_time = time.time()
        self.speed = 0  # 정지
        self.steering_angle = 0  # 정방향
        self.phase = 12
        self.status_message = "주차 완료! 2초 정지 중..."
    
    def check_parking_completion_stop(self):
        """주차 완료 후 2초 정지 완료 조건 확인"""
        if not self.parking_completion_stop_started or self.parking_completion_stop_start_time is None:
            return False
        
        elapsed_time = time.time() - self.parking_completion_stop_start_time
        stop_duration = 2.0  # 2초 정지
        
        if elapsed_time >= stop_duration:
            self.status_message = "2초 정지 완료! 정방향 직진 시작..."
            return True
        
        return False
    
    def start_initial_forward(self):
        """시뮬레이션 시작 - 초기 똑바로 전진"""
        self.speed = 2  # 전진 속도
        self.steering_angle = 0  # 똑바로
        self.initial_forward_started = True
        self.phase = 1
        self.status_message = "똑바로 전진 중..."
    
    def update(self):
        """차량 위치 업데이트"""
        if self.speed != 0:
            # 후진 중 조향각 점진적 조정 (5단계에서만 적용)
            if self.phase == 5 and self.backward_start_time is not None:
                elapsed_time = time.time() - self.backward_start_time
                # 2초에 걸쳐 조향각을 8도에서 0도로 줄임
                if elapsed_time < 2.0:
                    steering_reduction = (elapsed_time / 2.0) * 13
                    self.steering_angle = max(0, 13 - steering_reduction)
                else:
                    self.steering_angle = 0
            
            # 조향각에 따른 회전
            self.angle += self.steering_angle * 0.1 * (self.speed / abs(self.speed))
            
            # 위치 업데이트
            angle_rad = math.radians(self.angle)
            self.x += self.speed * math.cos(angle_rad)
            self.y += self.speed * math.sin(angle_rad)
    
    def draw(self, screen):
        """차량 그리기"""
        # 차량 몸체
        corners = []
        for dx, dy in [(-self.width/2, -self.height/2), (self.width/2, -self.height/2),
                       (self.width/2, self.height/2), (-self.width/2, self.height/2)]:
            angle_rad = math.radians(self.angle)
            x = self.x + dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
            y = self.y + dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
            corners.append((x, y))
        
        pygame.draw.polygon(screen, BLUE, corners)
        
        # 차량 방향 표시
        front_x = self.x + self.width/2 * math.cos(math.radians(self.angle))
        front_y = self.y + self.width/2 * math.sin(math.radians(self.angle))
        pygame.draw.circle(screen, YELLOW, (int(front_x), int(front_y)), 5)
        
        # 센서 그리기
        for sensor_name, rel_pos in self.sensor_positions.items():
            angle_rad = math.radians(self.angle)
            sensor_x = self.x + rel_pos[0] * math.cos(angle_rad) - rel_pos[1] * math.sin(angle_rad)
            sensor_y = self.y + rel_pos[0] * math.sin(angle_rad) + rel_pos[1] * math.cos(angle_rad)
            
            # 센서 위치
            color = GREEN if "right" in sensor_name else CYAN
            pygame.draw.circle(screen, color, (int(sensor_x), int(sensor_y)), 3)
            
            # 센서 레이
            if "right" in sensor_name:
                ray_angle = self.angle + 90  # 우측 센서는 오른쪽을 향함
            else:
                ray_angle = self.angle - 90  # 좌측 센서는 왼쪽을 향함
            
            ray_end_x = sensor_x + self.sensor_distances[sensor_name] * math.cos(math.radians(ray_angle))
            ray_end_y = sensor_y + self.sensor_distances[sensor_name] * math.sin(math.radians(ray_angle))
            
            pygame.draw.line(screen, color, (sensor_x, sensor_y), (ray_end_x, ray_end_y), 1)

class Obstacle:
    def __init__(self, x, y, width, height, is_car=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_car = is_car
    
    def draw(self, screen):
        if self.is_car:
            # 주차된 차량은 어두운 파란색 사각형으로 표시
            pygame.draw.rect(screen, (0, 0, 139), 
                           (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, BLACK, 
                           (self.x, self.y, self.width, self.height), 2)
        else:
            # 벽은 회색 사각형으로 표시
            pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height))

def main():
    clock = pygame.time.Clock()
    
    # 시뮬레이션 속도 설정 (FPS)
    simulation_speed = 60  # 기본 속도
    speed_multiplier = 0.5  # 속도 배율
    
    # 차량 생성 (주차장 아래에서 시작, 위를 향함)
    vehicle = Vehicle(300, 650)
    
    # 장애물 생성 (T자 주차 공간 시뮬레이션)
    # 주차 공간 위치 설정 - 차량 크기에 맞춰 조정
    parking_x = 350
    parking_y = 350
    parking_width = 80   # 차량 높이(30)의 약 2.7배
    parking_height = 50  # 차량 너비(60)와 동일
    parking_gap = 5     # 주차 공간 사이 간격 (20에서 10으로 줄임)
    
    # 장애물 차량 크기 (주차 공간의 80%)
    car_width = int(parking_width * 0.8)  # 64
    car_height = int(parking_height * 0.8)  # 48
    
    obstacles = [
        # 주차된 차량들 (사각형으로 표시) - 첫 번째와 세 번째 공간에만
        Obstacle(parking_x + (parking_width - car_width) // 2, 
                parking_y + (parking_height - car_height) // 2, 
                car_width, car_height, is_car=True),  # 위쪽 주차된 차
        
        # 중간 주차 공간은 비워둠 (우리 차량이 주차할 공간)
        
        Obstacle(parking_x + (parking_width - car_width) // 2, 
                parking_y + 2 * (parking_height + parking_gap) + (parking_height - car_height) // 2, 
                car_width, car_height, is_car=True),  # 아래쪽 주차된 차
    ]
    
    # 주차 공간 표시를 위한 점선 (3개 공간 모두)
    parking_spaces = [
        {
            'x': parking_x,
            'y': parking_y,
            'width': parking_width,
            'height': parking_height,
            'occupied': True
        },
        {
            'x': parking_x,
            'y': parking_y + parking_height + parking_gap,
            'width': parking_width,
            'height': parking_height,
            'occupied': False  # 빈 공간 (목표 주차 공간)
        },
        {
            'x': parking_x,
            'y': parking_y + 2 * (parking_height + parking_gap),
            'width': parking_width,
            'height': parking_height,
            'occupied': True
        }
    ]
    
    running = True
    simulation_started = False
    simulation_paused = False  # 일시정지 상태 변수 추가
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not simulation_started:
                        simulation_started = True
                    else:
                        # 이미 시작된 경우 일시정지/재개 토글
                        simulation_paused = not simulation_paused
                elif event.key == pygame.K_p:
                    # P 키로도 일시정지 가능
                    if simulation_started:
                        simulation_paused = not simulation_paused
                elif event.key == pygame.K_r:
                    # 리셋 - 처음과 동일한 위치로
                    vehicle = Vehicle(300, 650)
                    simulation_started = False
                    simulation_paused = False
                elif event.key == pygame.K_UP:
                    # 속도 증가 (더 빠르게)
                    speed_multiplier = min(speed_multiplier * 2, 8.0)
                elif event.key == pygame.K_DOWN:
                    # 속도 감소 (더 느리게)
                    speed_multiplier = max(speed_multiplier / 2, 0.125)
                elif event.key == pygame.K_1:
                    # 속도 1배 (정상 속도)
                    speed_multiplier = 1.0
                elif event.key == pygame.K_2:
                    # 속도 0.5배 (매우 느리게)
                    speed_multiplier = 0.5
                elif event.key == pygame.K_3:
                    # 속도 0.25배 (초저속)
                    speed_multiplier = 0.25
                elif event.key == pygame.K_c:
                    # C 키: 수정 완료 (10단계에서만 작동)
                    if vehicle.phase == 10 and vehicle.correction_started:
                        vehicle.complete_correction()
        
        # 화면 지우기
        screen.fill(WHITE)
        
        # 시뮬레이션 실행
        if simulation_started and not simulation_paused:
            # 센서 업데이트
            vehicle.update_sensors(obstacles)
            
            # 0단계: 초기 똑바로 전진 시작
            if vehicle.phase == 0 and not vehicle.initial_forward_started:
                vehicle.start_initial_forward()
            
            # 1단계: 첫 번째 정지 조건 확인
            if vehicle.phase == 1 and vehicle.initial_forward_started and not vehicle.first_stop_completed:
                if vehicle.check_stop_condition():
                    vehicle.stop_vehicle()
            
            # 2단계: 왼쪽 조향 전진 시작
            elif vehicle.phase == 2 and vehicle.first_stop_completed and not vehicle.left_turn_started:
                vehicle.start_left_turn_and_forward()
            
            # 3단계: 두 번째 정지 조건 확인
            elif vehicle.phase == 3 and vehicle.left_turn_started and not vehicle.second_stop_completed:
                if vehicle.check_second_stop_condition():
                    vehicle.stop_vehicle_second()
            
            # 4단계: 오른쪽 조향 후진 시작
            elif vehicle.phase == 4 and vehicle.second_stop_completed and not vehicle.right_turn_started:
                vehicle.start_right_turn_and_backward()
            
            # 5단계: 후진 완료 조건 확인
            elif vehicle.phase == 5 and vehicle.right_turn_started and not vehicle.backward_completed:
                if vehicle.check_backward_completion():
                    vehicle.stop_backward()
            
            # 6단계: 정방향 후진 완료 조건 확인
            elif vehicle.phase == 6 and vehicle.straight_backward_started:
                if vehicle.check_straight_backward_completion():
                    vehicle.complete_straight_backward()
            
            # 7단계: 정렬 시작
            elif vehicle.phase == 7 and vehicle.backward_completed and not vehicle.alignment_completed:
                vehicle.start_alignment()
            
            # 8단계: 정렬 완료 조건 확인
            elif vehicle.phase == 8 and not vehicle.alignment_completed:
                if vehicle.check_alignment_completion():
                    vehicle.complete_alignment()
            
            # 9단계: 위치 수정 필요 여부 확인
            elif vehicle.phase == 9 and vehicle.alignment_completed:
                if vehicle.check_position_correction_needed():
                    vehicle.start_correction()
                else:
                    # 수정이 필요하지 않은 경우 주차 완료 후 2초 정지 시작
                    vehicle.start_parking_completion_stop()
            
            # 10단계: 위치 수정 (로직 미구현)
            elif vehicle.phase == 10 and vehicle.correction_started:
                # 좌측 치우침 수정 로직
                if vehicle.left_correction_started:
                    if vehicle.check_left_correction_completion():
                        vehicle.complete_correction()
                # 우측 치우침 수정 로직
                elif vehicle.right_correction_started:
                    if vehicle.check_right_correction_completion(): # 좌측 치우침 수정 로직과 동일한 형태로 변경
                        vehicle.complete_correction()
                # 현재는 수정 중 상태를 유지 (메시지 계속 표시)
                pass
            
            # 11단계: 수정 후 정방향 후진 시작
            elif vehicle.phase == 11 and vehicle.correction_completed and not vehicle.post_correction_backward_started:
                vehicle.start_post_correction_backward()
            
            # 12단계: 수정 후 정방향 후진 완료 조건 확인
            elif vehicle.phase == 11 and vehicle.post_correction_backward_started:
                if vehicle.check_post_correction_backward_completion():
                    vehicle.complete_post_correction_backward()
            
            # 12단계: 주차 완료 후 2초 정지 확인
            elif vehicle.phase == 12 and vehicle.parking_completion_stop_started:
                if vehicle.check_parking_completion_stop():
                    vehicle.start_parking_completion_forward()
            
            # 12단계: 주차 완료 후 정방향 직진 시작
            elif vehicle.phase == 12 and not vehicle.parking_completion_forward_started and not vehicle.parking_completion_stop_started:
                vehicle.start_parking_completion_forward()
            
            # 13단계: rear_right 갑작스러운 증가 감지 및 오른쪽 조향
            elif vehicle.phase == 13 and vehicle.parking_completion_forward_started:
                if not vehicle.right_turn_after_increase_started and vehicle.check_rear_right_sudden_increase():
                    vehicle.start_right_turn_after_increase()
                elif vehicle.right_turn_after_increase_started and vehicle.check_right_turn_completion():
                    vehicle.start_final_forward()
            
            # 차량 위치 업데이트
            vehicle.update()
        elif simulation_started and simulation_paused:
            # 일시정지 상태에서도 센서는 업데이트 (시각적 표시를 위해)
            vehicle.update_sensors(obstacles)
        
        # 그리기
        for obstacle in obstacles:
            obstacle.draw(screen)
        
        # 주차 공간 점선 표시
        if 'parking_spaces' in locals():
            for parking_space in parking_spaces:
                # 빈 공간은 더 밝은 색으로 표시
                line_color = (255, 200, 0) if not parking_space.get('occupied', False) else (150, 150, 150)
                line_width = 3 if not parking_space.get('occupied', False) else 2
                
                # 주차 공간을 점선으로 표시
                dash_length = 10
                gap_length = 5
                
                # 세로 점선 (좌)
                y = parking_space['y']
                while y < parking_space['y'] + parking_space['height']:
                    pygame.draw.line(screen, line_color, 
                                   (parking_space['x'], y), 
                                   (parking_space['x'], min(y + dash_length, parking_space['y'] + parking_space['height'])), 
                                   line_width)
                    y += dash_length + gap_length
                
                # 세로 점선 (우)
                y = parking_space['y']
                while y < parking_space['y'] + parking_space['height']:
                    pygame.draw.line(screen, line_color, 
                                   (parking_space['x'] + parking_space['width'], y), 
                                   (parking_space['x'] + parking_space['width'], 
                                    min(y + dash_length, parking_space['y'] + parking_space['height'])), 
                                   line_width)
                    y += dash_length + gap_length
                
                # 목표 주차 공간 표시
                if not parking_space.get('occupied', False):
                    # 'P' 문자 표시
                    p_text = big_font.render("P", True, ORANGE)
                    text_rect = p_text.get_rect(center=(parking_space['x'] + parking_space['width']//2, 
                                                       parking_space['y'] + parking_space['height']//2))
                    screen.blit(p_text, text_rect)
        
        vehicle.draw(screen)
        
        # UI 정보 표시
        y_offset = 20
        
        # 제목
        title_text = big_font.render("차량 주차 시뮬레이션", True, BLACK)
        screen.blit(title_text, (WIDTH - 350, y_offset))
        y_offset += 40
        
        # 센서 거리 정보
        screen.blit(font.render("센서 거리 (cm):", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 30
        
        for sensor_name, distance in vehicle.sensor_distances.items():
            color = GREEN if "right" in sensor_name else CYAN
            text = font.render(f"{sensor_name}: {distance:.1f}", True, color)
            screen.blit(text, (WIDTH - 350, y_offset))
            y_offset += 25
        
        # 상태 정보
        y_offset += 20
        screen.blit(font.render(f"단계: {vehicle.phase}/14", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 30
        screen.blit(font.render(f"상태: {vehicle.status_message}", True, RED), (WIDTH - 350, y_offset))
        
        # 2초 정지 중일 때 남은 시간 표시
        if vehicle.parking_completion_stop_started and vehicle.parking_completion_stop_start_time is not None:
            elapsed_time = time.time() - vehicle.parking_completion_stop_start_time
            remaining_time = max(0, 2.0 - elapsed_time)
            y_offset += 30
            screen.blit(font.render(f"정지 남은 시간: {remaining_time:.1f}초", True, ORANGE), (WIDTH - 350, y_offset))
        
        # 센서 감지 상태 표시
        y_offset += 30
        screen.blit(font.render("센서 감지 상태:", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        for sensor_name, detected in vehicle.sensor_flags.items():
            color = GREEN if detected else RED
            status = "감지됨" if detected else "대기중"
            text = font.render(f"{sensor_name}: {status}", True, color)
            screen.blit(text, (WIDTH - 350, y_offset))
            y_offset += 20
        
        # 조작 방법
        y_offset = HEIGHT - 100
        screen.blit(font.render("조작 방법:", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        if not simulation_started:
            screen.blit(font.render("SPACE: 시뮬레이션 시작", True, BLACK), (WIDTH - 350, y_offset))
        else:
            if simulation_paused:
                screen.blit(font.render("SPACE/P: 재개", True, GREEN), (WIDTH - 350, y_offset))
            else:
                screen.blit(font.render("SPACE/P: 일시정지", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        screen.blit(font.render("R: 리셋", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        screen.blit(font.render("UP/DOWN: 속도 조절", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        screen.blit(font.render("1/2/3: 속도 프리셋", True, BLACK), (WIDTH - 350, y_offset))
        y_offset += 25
        screen.blit(font.render("C: 수정 완료 (10단계)", True, BLACK), (WIDTH - 350, y_offset))
        
        # 현재 속도 표시
        y_offset += 25
        speed_text = f"속도: {speed_multiplier:.2f}x"
        screen.blit(font.render(speed_text, True, BLUE), (WIDTH - 350, y_offset))
        
        # 일시정지 상태 표시
        if simulation_paused:
            pause_text = big_font.render("일시정지", True, RED)
            text_rect = pause_text.get_rect(center=(WIDTH//2, 50))
            pygame.draw.rect(screen, WHITE, text_rect.inflate(20, 10))
            pygame.draw.rect(screen, RED, text_rect.inflate(20, 10), 3)
            screen.blit(pause_text, text_rect)
        
        # 단계 설명
        phase_descriptions = [
            "0단계: 똑바로 전진",
            "1단계: 우측 센서로 차량 감지",
            "2단계: 첫 번째 정지",
            "3단계: 왼쪽 조향 후 전진",
            "4단계: 두 번째 정지",
            "5단계: 오른쪽 조향 후 후진 주차",
            "6단계: 후진 완료 + 정방향 후진",
            "7단계: 정방향 후진 완료",
            "8단계: 차량 정렬",
            "9단계: 주차 완료",
            "10단계: 위치 수정 필요",
            "11단계: 수정 후 정방향 후진",
            "12단계: 주차 완료 후 2초 정지",
            "13단계: 정방향 직진",
            "14단계: rear_right 증가 후 오른쪽 조향"
        ]
        
        y_offset = 100
        screen.blit(font.render("T자 주차 진행 단계:", True, BLACK), (20, y_offset))
        y_offset += 30
        for i, desc in enumerate(phase_descriptions):
            color = ORANGE if i == vehicle.phase else BLACK
            screen.blit(font.render(desc, True, color), (20, y_offset))
            y_offset += 25
        
        # 주차 팁 표시
        y_offset += 20
        screen.blit(font.render("주차 과정:", True, BLACK), (20, y_offset))
        y_offset += 25
        tips = [
            "① 주차 공간 옆을 지나가며 감지",
            "② 적절한 위치에서 정지",
            "③ 좌회전하며 전진",
            "④ 후진 준비 위치에서 정지",
            "⑤ 우회전하며 후진 주차"
        ]
        for tip in tips:
            screen.blit(font.render(tip, True, (100, 100, 100)), (20, y_offset))
            y_offset += 20
        
        pygame.display.flip()
        clock.tick(int(simulation_speed * speed_multiplier))
    
    pygame.quit()

if __name__ == "__main__":
    main()