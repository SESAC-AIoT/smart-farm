# SESAC_Project_Cat-grass-AIoT-Smart-Farm

### 🎈 Project Team R&R
* FarmBoys (맹광국, 송명근, 박태현)

### 🎈 Project Schedule
1. 준비(2/06-2/10) : 매일 1시간 주제 아이데이션
2. 1주차(2/13-2/15) : 주제 확정 및 피처 선정, RnR, 개발환경 구성, 기술 사전 조사, 문서화(기획/WBS), 2/15 기획 발표(킥오프), 2/16-17 개발 시작
3. 2주차(2/20-2/24) : 20일 중간 통합, 21~23 기능 추가, 24 통합 서비스 배포
4. 발표(2/27-28) : 27일 문서화/정리, 28일 발표

### 🎈 Project Goal
1. 공부 내용이 최대한 활용/반영된 서비스 포트폴리오 만들기
2. 확실한 완성을 위해 스펙은 작게 시작해서 살을 붙이는 방식으로
3. 리소스절약 위해 기획/디자인/리서치/데이터수집 등 최소한으로

### 🎈 Project Rule
* 개인별 관심사/우선순위/리소스를 존중하고 스펙 조율
* 협업을 위해 task를 구성하되 특이사항을 고려

### 🎈 Project Management & Collaboration Tool 
* Agile + Waterfall Hybrid, Daily Scrum
<img width="401" alt="Agile+Waterfall Hybrid" src="https://user-images.githubusercontent.com/79052421/221502124-c2011b62-8c21-42ad-91f8-535b8e6d901d.png">
* Messenger(Slack), Code(Github Organization)
* Task(Github Projects), Issue(Github Issues), Documentation(Notion/Google)
 
### 1. Subject
* Cat grass AIoT Smart Farm (Cat Farm)
* 요약 : 반려묘 가정 필수 식물인 캣그라스를 잘 키울 수 있도록 생육 환경(온습도 등)을 관리하고 모니터링할 수 있는 AIoT 웹 서비스
* 캣그라스 란? 귀리, 밀, 보리 호밀 등 고양이가 먹어도 안전한 풀로서 고양이 건강(헤어볼/배변 배출, 미네랄/비타민 섭취)관리 목적으로 키움
<img width="538" alt="image" src="https://user-images.githubusercontent.com/79052421/221502262-f33ff0ab-990f-41d5-b99c-340976f07760.png">

### 2. Problem(Pain Point/Needs)
* 똥손 집사라서 미안해
* 비교적 키우기 쉬운 식물에 속하지만 식물 똥손에게 난이도는 무관하다.
* 온습도를 맞추기 못해 곰팡이가 슬고 겨울철엔 성장에 더욱 더디다.
<img width="408" alt="image" src="https://user-images.githubusercontent.com/79052421/221502317-fcc28cd9-3a9e-4992-81d4-30a054265633.png">

### 3. Solution Ideation
* 똥손 집사를 위한 “캣그라스”전용 가정용 스마트팜
* 적정 캣그라스 생육 환경과 생육 정보 대시보드를 제공한다. 또한, 미성숙한 캣그라스순에 대한 고양이 접근을 막기 위해 탐지 알림을 준다.

### 4. Core Features
1. 생육 환경 센서 수집 및 디바이스 컨트롤
2. 고양이 탐지 알림 및 로그 대시보드
3. 센서 데이터 관제 대시보드
<img width="297" alt="image" src="https://user-images.githubusercontent.com/79052421/221505082-c76b3fdc-7775-41ba-96cf-7fac07a1da68.png">

### 5. Service Architecture
<img width="326" alt="image" src="https://user-images.githubusercontent.com/79052421/221504330-6076b263-ce1f-464f-bd78-a78b665f20f4.png">

### 6. Developement Framework (requirements.txt 참고)
* Language : Python 3.10.9
* IDE : Pycharm, Cobal, Jupyter notebook
* OS : Linux(Ubuntu server), Windows11(Local PC)
* GPU/Cuda : NVIDIA GeForce RTX 3070 Ti, 8192MiB, CU113
* Server : Cloud Service( DBMS-NoSQL, Storage-CDN )
* Web App : python-Flask
* Model : YOLOv5(Python-Pytorch)

### 7. Device/Sensor List
1) Base / Board : [Converea(교육용 스마트팜)](https://youtu.be/L2TvesXuN0w)
<img width="491" alt="image" src="https://user-images.githubusercontent.com/79052421/221507315-73264cbf-c0c5-40f7-af6c-f21076f0b7c5.png">

2) Edge Computing : Jetson Nano 4G, Raspberry pi 4
<img width="513" alt="image" src="https://user-images.githubusercontent.com/79052421/221507027-de5e7211-4800-4e49-a1a6-ec4313218770.png">
<img width="481" alt="image" src="https://user-images.githubusercontent.com/79052421/221506752-65a9cff0-460e-42c9-a62a-f7756c7cbcde.png">

3) Actuator : 수중펌프모터, 환기 팬

5) Sensor : 온습도센서, 수온센서, 비접촉 수위센서, PH센서, 탁도센서

7) Web cam

### 8. WBS
<img width="719" alt="image" src="https://user-images.githubusercontent.com/79052421/221506515-cbbef6af-ce66-4666-8c45-60edd3a637fd.png">

### 9. Directory Description
* device
ㄴ jetsonNano_0.6v.py : 식물 성장 분류 모델 예측 및 파베 업로드 코드
ㄴ raspBerryPi_0.6v.py : 컨버리아 센서데이터 수집/가공 및 파베 업로드 코드
* webApp
ㄴ static
    ㄴ CSS/
    ㄴ secret/ : 모델/인증키/아웃풋 (git ignore)
    ㄴ src files
ㄴ templates : web page
ㄴ app.py : flask 웹서버 어플리케이션 코드
ㄴ database.py : 파이어베이스 접속/인증/생성 코드
ㄴ fake_data_gen.py : aiot 디바이스 없을 때 대비, 가짜 센서 데이터 제너레이터
* venv : 가상 환경(git ignore)