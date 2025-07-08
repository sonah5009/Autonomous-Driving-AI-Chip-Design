import math
import time

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

class Obstacle:
    def __init__(self, x, y, width, height, is_car=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_car = is_car 