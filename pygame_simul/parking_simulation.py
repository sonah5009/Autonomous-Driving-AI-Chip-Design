import pygame
import math
import random
import time
from parking_algorithm import Vehicle, Obstacle

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

def draw_vehicle(screen, vehicle):
    """차량 그리기"""
    # 차량 몸체
    corners = []
    for dx, dy in [(-vehicle.width/2, -vehicle.height/2), (vehicle.width/2, -vehicle.height/2),
                   (vehicle.width/2, vehicle.height/2), (-vehicle.width/2, vehicle.height/2)]:
        angle_rad = math.radians(vehicle.angle)
        x = vehicle.x + dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        y = vehicle.y + dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        corners.append((x, y))
    
    pygame.draw.polygon(screen, BLUE, corners)
    
    # 차량 방향 표시
    front_x = vehicle.x + vehicle.width/2 * math.cos(math.radians(vehicle.angle))
    front_y = vehicle.y + vehicle.width/2 * math.sin(math.radians(vehicle.angle))
    pygame.draw.circle(screen, YELLOW, (int(front_x), int(front_y)), 5)
    
    # 센서 그리기
    for sensor_name, rel_pos in vehicle.sensor_positions.items():
        angle_rad = math.radians(vehicle.angle)
        sensor_x = vehicle.x + rel_pos[0] * math.cos(angle_rad) - rel_pos[1] * math.sin(angle_rad)
        sensor_y = vehicle.y + rel_pos[0] * math.sin(angle_rad) + rel_pos[1] * math.cos(angle_rad)
        
        # 센서 위치
        color = GREEN if "right" in sensor_name else CYAN
        pygame.draw.circle(screen, color, (int(sensor_x), int(sensor_y)), 3)
        
        # 센서 레이
        if "right" in sensor_name:
            ray_angle = vehicle.angle + 90  # 우측 센서는 오른쪽을 향함
        else:
            ray_angle = vehicle.angle - 90  # 좌측 센서는 왼쪽을 향함
        
        ray_end_x = sensor_x + vehicle.sensor_distances[sensor_name] * math.cos(math.radians(ray_angle))
        ray_end_y = sensor_y + vehicle.sensor_distances[sensor_name] * math.sin(math.radians(ray_angle))
        
        pygame.draw.line(screen, color, (sensor_x, sensor_y), (ray_end_x, ray_end_y), 1)

def draw_obstacle(screen, obstacle):
    """장애물 그리기"""
    if obstacle.is_car:
        # 주차된 차량은 어두운 파란색 사각형으로 표시
        pygame.draw.rect(screen, (0, 0, 139), 
                       (obstacle.x, obstacle.y, obstacle.width, obstacle.height))
        pygame.draw.rect(screen, BLACK, 
                       (obstacle.x, obstacle.y, obstacle.width, obstacle.height), 2)
    else:
        # 벽은 회색 사각형으로 표시
        pygame.draw.rect(screen, GRAY, (obstacle.x, obstacle.y, obstacle.width, obstacle.height))

def draw_parking_spaces(screen, parking_spaces):
    """주차 공간 점선 표시"""
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

def draw_ui(screen, vehicle, simulation_started, simulation_paused, speed_multiplier):
    """UI 정보 표시"""
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
            draw_obstacle(screen, obstacle)
        
        # 주차 공간 점선 표시
        draw_parking_spaces(screen, parking_spaces)
        
        # 차량 그리기
        draw_vehicle(screen, vehicle)
        
        # UI 정보 표시
        draw_ui(screen, vehicle, simulation_started, simulation_paused, speed_multiplier)
        
        pygame.display.flip()
        clock.tick(int(simulation_speed * speed_multiplier))
    
    pygame.quit()

if __name__ == "__main__":
    main() 