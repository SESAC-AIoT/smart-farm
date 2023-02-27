# SESAC_Project_Cat-grass-AIoT-Smart-Farm

### 🎈 Project Team R&R
* FarmBoys (맹광국, 송명근, 박태현/송애경)

### 🎈 Project Schedule
1. 준비(2/06~2/10) : 매일 1시간 주제 아이데이션
2. 1주차(2/13~2/15) : 주제 확정 및 피처 선정, RnR, 개발환경 구성, 기술 사전 조사, 문서화(기획/WBS), 2/15 기획 발표(킥오프), 2/16~17 개발 시작
3. 2주차(2/20~2/24) : 20일 중간 통합, 21~23 기능 추가, 24 통합 서비스 배포
4. 발표(2/27~28) : 27일 문서화/정리, 28일 발표

### 🎈 Project Goal
1. 공부 내용이 최대한 활용/반영된 서비스 포트폴리오 만들기
2. 확실한 완성을 위해 스펙은 작게 시작해서 살을 붙이는 방식으로
3. 리소스절약 위해 기획/디자인/리서치/데이터수집 등 최소한으로

### 🎈 Project Rule
* 개인별 관심사/우선순위/리소스를 존중하고 스펙 조율
* 협업을 위해 task를 구성하되 특이사항을 고려

### 🎈 Project Management & Collaboration Tool 
* Agile + Waterfall Hybrid, Daily Scrum
* Messenger(Slack), Code(Github Organization)
* Task(Github Projects), Issue(Github Issues), Documentation(Notion/Google)
 
### 1. Subject
* Cat grass AIoT Smart Farm (Cat Farm)
* 요약 : 반려묘 가정 필수 식물인 캣그라스를 잘 키울 수 있도록 생육 환경(온습도 등)을 관리하고 모니터링할 수 있는 AIoT 웹 서비스
* 캣그라스 란? 귀리, 밀, 보리 호밀 등 고양이가 먹어도 안전한 풀로서 고양이 건강(헤어볼/배변 배출, 미네랄/비타민 섭취)관리 목적으로 키움

### 2. Problem(Pain Point/Needs)
* 똥손 집사라서 미안해
* 비교적 키우기 쉬운 식물에 속하지만 식물 똥손에게 난이도는 무관하다.
* 온습도를 맞추기 못해 곰팡이가 슬고 겨울철엔 성장에 더욱 더디다.

### 3. Solution Ideation
* 똥손 집사를 위한 “캣그라스”전용 가정용 스마트팜
* 적정 캣그라스 생육 환경과 생육 정보 대시보드를 제공한다. 또한, 미성숙한 캣그라스순에 대한 고양이 접근을 막기 위해 탐지 알림을 준다.

### 4. Core Features
1. 생육 환경 센서 수집 및 디바이스 컨트롤
2. 고양이 탐지 알림 및 로그 대시보드
3. 센서 데이터 관제 대시보드

### 5. Service Architecture

### 6. Developement Framework
* Language : Python
* IDE : Pycharm, Cobal, Jupyter notebook
* OS : Linux(Ubuntu server), Windows11(Local PC)
* Server : Cloud Service( DBMS-NoSQL, Storage-CDN )
* Web App : python-Flask
* Model : YOLOv5(Python-Pytorch)

### 7. Device/Sensor List
1) Base / Board : [Converea(교육용 스마트팜)](https://youtu.be/L2TvesXuN0w)
2) Edge Computing : Jetson Nano 4G, Raspberry pi 4
3) Actuator : 수중펌프모터, 환기 팬
4) Sensor : 온습도센서, 수온센서, 비접촉 수위센서, PH센서, 탁도센서
5) Web cam