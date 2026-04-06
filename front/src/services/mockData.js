export const systemMetrics = [
  { label: '复杂天气覆盖', value: '4+', note: '雨 / 雪 / 雾 / 夜间' },
  { label: '目标类别', value: '3', note: '车辆 / 行人 / 交通标志' },
  { label: '可切换算法', value: '2', note: '改进 YOLO / Faster R-CNN' },
  { label: '输出维度', value: '5', note: '检测框 / 分数 / 风险 / 场景 / 建议' },
]

export const scenarioCards = [
  {
    key: 'rain',
    title: 'Rainy Urban',
    description: '重点处理反光、路面积水和雨滴遮挡下的车辆与行人误检问题。',
  },
  {
    key: 'snow',
    title: 'Snowy Road',
    description: '针对雪幕、轮廓模糊和背景白化情况提升小目标识别能力。',
  },
  {
    key: 'fog',
    title: 'Foggy Highway',
    description: '结合去雾增强与远距离目标感知，缓解能见度下降带来的漏检。',
  },
  {
    key: 'night',
    title: 'Night Intersection',
    description: '通过低照度增强与高亮区域抑制，提高夜间交通标志和行人检测稳定性。',
  },
]

export const workflowSteps = [
  '输入图像或视频帧',
  '复杂天气类型识别',
  '低能见度增强预处理',
  '改进 YOLO / Faster R-CNN 推理',
  '多目标检测结果可视化',
  '场景风险评估与辅助决策输出',
]

export const defaultDetections = [
  {
    id: 1,
    label: 'vehicle',
    score: 0.94,
    left: '9%',
    top: '42%',
    width: '26%',
    height: '23%',
    risk: 'medium',
  },
  {
    id: 2,
    label: 'pedestrian',
    score: 0.89,
    left: '60%',
    top: '38%',
    width: '10%',
    height: '26%',
    risk: 'high',
  },
  {
    id: 3,
    label: 'traffic_sign',
    score: 0.81,
    left: '74%',
    top: '18%',
    width: '8%',
    height: '14%',
    risk: 'low',
  },
]

export const riskDistribution = [
  { label: '高风险', value: 2, accent: 'var(--danger)' },
  { label: '中风险', value: 5, accent: 'var(--warning)' },
  { label: '低风险', value: 9, accent: 'var(--success)' },
]

export const weatherStrategies = [
  {
    title: '雨天增强策略',
    text: '提升边缘纹理保留能力，抑制雨丝干扰，降低车灯反光造成的误识别。',
  },
  {
    title: '雾天增强策略',
    text: '使用对比度恢复和可见性增强，提高远距离车辆与交通标志检测率。',
  },
  {
    title: '夜间增强策略',
    text: '强化暗光区域可感知特征，并抑制高亮光斑对检测框稳定性的影响。',
  },
]
