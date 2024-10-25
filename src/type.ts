export interface ICourse {
  /**
   * 可以选择
   */
  canSelect: '0' | '1';
  /**
   * 可以删选
   */
  canDelete: '0' | '1';
  /**
   * 不检测课程容量
   */
  noCheckKrl: '0' | '1';
  /**
   * 答疑时间
   * 如：'一3-4'
   */
  answerTime?: string;
  /**
   * 答疑地点
   * 如：'F413'
   */
  answerPlace?: string;
  /**
   * 选课限制
   * 如：无限制
   */
  selectLimit?: string;
  limitNumberName: string;
  /**
   * 方案 1 选课人数
   */
  FAXKRS1: number;
  /**
   * 方案 2 选课人数
   */
  FAXKRS2: number;
  /**
   * 方案 3 选课人数
   */
  FAXKRS3: number;
  /**
   * 选满锁定(检测课程容量)课程的选课人数
   */
  YXRS: number;
  /**
   * 非选满锁定(不检测课程容量)课程的选课人数
   */
  YXRS2: number;
  /**
   * 研究生课程容量
   */
  YJSKRL: number;
  /**
   * 研究生选课人数
   */
  YJSXKRS: number;
  trainingCode: string[] | undefined;
  /**
   * 公共课程
   */
  isPublicCourse: '0' | '1';
  teachCampus: '01';
  /**
   * 限制性别
   */
  SFXZXB: '0' | '1';
  isRetakeClass: '3';
  department: '03040000';
  /**
   * 先修课程
   * 如：1
   */
  preCourseName: string;
  /**
   * 男生课容量
   */
  NSKRL: number;
  /**
   * 女生课容量
   */
  NVSKRL: number;
  /**
   * 男生选课人数
   */
  NSXKRS: number;
  /**
   * 女生选课人数
   */
  NVSXKRS: number;
  limitKindList: {
    wid: '2326FAD9500630C3E0638D000A0ADF4E';
    teachingClassID: '202420252000000001001';
    code: '11';
    name: '院系';
    limitType: '1';
    limitValue: '01250000';
    limitDesc: '中欧工程技术学院';
    childLimitKind: [];
  }[];
  /**
   * 上课时间
   */
  SKSJ: {
    /**
     * 教学班 ID
     * 如：'202420252000000001001'
     */
    teachingClassID: string;
    /**
     * 课程号
     * 如：'00000000'
     */
    KCH: string;
    /**
     * 课程名称
     * 如：'活动课'
     */
    KCM: string;
    /**
     * 上课周次
     * 如：'1111111111'
     */
    SKZC: string;
    /**
     * 上课周次名称
     * 如：'1-10周'
     */
    SKZCMC: string;
    /**
     * 上课星期
     * 如：'3'
     */
    SKXQ: string;
    /**
     * 开始节次
     * 如：'7'
     */
    KSJC: string;
    /**
     * 结束节次
     * 如：'8'
     */
    JSJC: string;
    /**
     * 时间类型
     * 如：'1'
     */
    timeType: string;
    /**
     * 课序号（教师号）
     * 如：'1001'
     */
    KXH: string;
  }[];
  /**
   * 开课学期
   */
  schoolTerm: string;
  /**
   * (教学班 ID?)
   */
  JXBID: '202420252000000001001';
  /**
   * 校区
   * 如：1
   */
  campus: '1';
  /**
   * 校区
   * 如：宝山
   */
  XQ: string;
  /**
   * 课程号
   * 如：20624020
   */
  KCH: string;
  /**
   * 课程名称
   * 如：活动课
   */
  KCM: string;
  /**
   * 课序号（教师号）
   * 如：1001
   */
  KXH: string;
  /**
   * 上课教师
   * 如：赵凤珍
   */
  SKJS?: string;
  /**
   * 上课教师标签
   * 如：小学高级教师|10008024
   */
  SKJSLB: string;
  /**
   * 开课单位
   * 如：教务部
   */
  KKDW: string;
  /**
   * 上课时间
   * 如：三7-8 限钱院
   */
  teachingPlace: string;
  teachingPlaceHide: '';
  /**
   * 学时
   */
  XS: '0';
  /**
   * 学分
   * 如：30
   */
  XF: '0';
  hasTest: '0';
  isTest: '0';
  hasBook: '0';
  numberOfSelected: 0;
  numberOfFirstVolunteer: 0;
  /**
   * 班级容量
   * 如：30
   */
  classCapacity: number;
  /**
   * 课程性质
   * 如：选修
   */
  KCXZ: string;
  /**
   * 课程类别
   * 如：任意选修课
   */
  KCLB: '任意选修课';
  courseType: '02';
  courseNature: '02';
  schoolClassMapStr: '';
  /**
   * 上课教师职称
   * 如：讲师
   */
  SKJSZC: string;
  /**
   * 课程容量
   */
  KRL: number;
  /**
   * 第一志愿人数
   */
  DYZYRS: 0;
  SFYX: '';
  /**
   * 课程是否已经选满
   */
  SFYM: '0' | '1';
  secretVal: string;
  /**
   * 是否冲突
   */
  SFCT: '0' | '1';
  SFXZXK: '';
  XGXKLB: '';
  DGJC: '';
  SFKT: '1';
  conflictDesc: '';
  testTeachingClassID: '';
  /**
   * 上课时间地点
   */
  YPSJDD: '三7-8 限钱院';
  ZYDJ: '';
  KSLX: '';
  XDFS: '01';
  SFSC: '';
}

export interface ISimpleCourse {
  /**
   * 课程号
   */
  courseId: string;
  /**
   * 课程名
   */
  courseName: string;
  /**
   * 学分
   */
  credit: string;
  /**
   * 教师号
   */
  teacherId: string;
  /**
   * 教师名
   */
  teacherName: string;
  /**
   * 教师职称
   */
  teacherTitle: string;
  /**
   * 上课时间
   */
  classTime: string;
  /**
   * 上课校区
   */
  campus: string;
  /**
   * 上课地点
   */
  position: string;
  /**
   * 课程容量
   */
  capacity: string;
  /**
   * 选课人数
   */
  number: string;
  /**
   * 选课限制
   */
  limitations: string[];
}

export interface IElectiveBatch {
  bybz: string; // '0';
  beginTime2: string; // '2024-10-18 20:30:00';
  endTime2: string; // '2024-10-23 08:00:00';
  beginTime3: string; // '2024-11-01 20:30:00';
  endTime3: string; // '2024-11-06 08:00:00';
  code: string; // '23d4bd1b8188422bbbba6606989b20b0';
  name: string; // '2024-2025学年冬季学期';
  canSelect: string; // '1';
  schoolTerm: string; // '2024-2025-2';
  beginTime: string; // '2024-10-11 20:30:00';
  endTime: string; // '2024-10-16 08:00:00';
  tacticCode: string; // '01';
  typeCode: string; // '02';
  typeName: string; // '正选';
  isConfirmed: string; // '0';
  schoolTermName: string; // '2024-2025学年冬季学期';
  weekRange: string; // '1-10周';
  canSelectBook: string; // '0';
  canDeleteBook: string; // '0';
  multiCampus: string; // '1';
  multiTeachCampus: string; // '1';
  noCheckTimeConflict: string; // '0';
}
