
create database universitydb;

grant all privileges on universitydb.* to ohgiraffers@'%';

use universitydb;


CREATE TABLE `school_info` (
 `school_id` INT AUTO_INCREMENT COMMENT '학교 코드',
 `school_name` VARCHAR(100) NOT NULL COMMENT '학교 이름',
 `country` VARCHAR(20) NOT NULL COMMENT '나라 이름',
 `location` TEXT NOT NULL COMMENT '대학교 주소',
 PRIMARY KEY(`school_id`)
) ENGINE = INNODB COMMENT = '대학교 정보';

# not null 최종적으로 확인 필요
CREATE TABLE `admission_info` (
 `admission_id` INT AUTO_INCREMENT COMMENT '입시 지원 코드',
 `school_id` INT NOT NULL COMMENT '학교 코드',
 `tuition` INT NULL COMMENT '학비',
 `regular_deadline_date` DATE NULL COMMENT '정규학기 마감일자',
 `early_deadline_date` DATE NULL COMMENT '조기지원 마감일자',
 PRIMARY KEY(`admission_id`),
 CONSTRAINT fk_adm_school FOREIGN KEY (`school_id`) REFERENCES `school_info` (`school_id`) 
) ENGINE = INNODB COMMENT = '입시 정보';

CREATE TABLE `requirement_info` (
 `req_id` INT AUTO_INCREMENT COMMENT '요구사항 코드',
 `school_id` INT NOT NULL COMMENT '학교 코드',
 `requirement_type` VARCHAR(100) NULL COMMENT '제출서류타입',
 `metric_type` VARCHAR(100) NULL COMMENT '타입 별 하위 분류',
 `requirement_require` VARCHAR(100) NULL DEFAULT 0 COMMENT '요구 조건 여부',
 `requirement_value` TEXT NULL COMMENT '제출 서류 별 점수',
 `notes` TEXT NULL COMMENT '서류 제출 시 추가사항',
 PRIMARY KEY(`req_id`),
 CONSTRAINT fk_req_school FOREIGN KEY (`school_id`) REFERENCES `school_info` (`school_id`) 
) ENGINE = INNODB COMMENT = '입시 요구사항 정보';

CREATE TABLE faq_info (
    qna_id INT AUTO_INCREMENT comment 'qna 코드',
    school_id INT NOT NULL COMMENT '학교 코드',
    question TEXT comment '질문',
    answer TEXT comment '응답',
    category VARCHAR(100) comment '질문 카테고리',
    PRIMARY KEY(qna_id),
    CONSTRAINT school_id FOREIGN KEY (school_id) REFERENCES school_info(school_id)
) ENGINE = INNODB COMMENT = '질의응답';

DROP TABLE IF EXISTS requirement_info CASCADE;
DROP TABLE IF EXISTS admission_info CASCADE;
DROP TABLE IF EXISTS faq_info CASCADE;
DROP TABLE IF EXISTS school_info CASCADE;


select * from faq_info;

