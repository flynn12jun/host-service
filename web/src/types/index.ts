// ==================== 模型相关 ====================

export interface AvailableModel {
  name: string
  provider: string
  available: boolean
}

// ==================== 枚举定义 ====================

export enum AgentRole {
  OPERATIONS_DIRECTOR = 'operations_director',
  NUTRITIONIST = 'nutritionist',
  RD_CHEF = 'rd_chef',
  HEAD_CHEF = 'head_chef',
}

export enum AgentStatus {
  IDLE = 'idle',
  PROCESSING = 'processing',
  WAITING_REVIEW = 'waiting_review',
  COMPLETED = 'completed',
  REJECTED = 'rejected',
}

export enum WorkflowStatus {
  CREATED = 'created',
  EXTRACTING = 'extracting',
  NUTRITION_DESIGNING = 'nutrition_designing',
  CONCEPT_DESIGNING = 'concept_designing',
  RECIPE_REVIEWING = 'recipe_reviewing',
  WAITING_APPROVAL = 'waiting_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  REVISING = 'revising',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// ==================== Agent 相关 ====================

export interface Agent {
  role: AgentRole
  name: string
  description: string
  status: AgentStatus
  current_task?: string
  output?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface AgentStatusInfo {
  role: string
  name: string
  status: string
  current_task?: string
}

// ==================== 运营总监输出 ====================

export interface OperationsDirectorOutput {
  task_type: 'dish' | 'group_meal'
  dish_requirements?: {
    flavor: string[]
    cooking_method: string
    ingredient_restrictions: string[]
  }
  nutrition_requirements?: {
    calories_range: [number, number]
    protein_min: number
    fat_max: number
    special_diet: string[]
  }
  group_meal_info?: {
    people_count: number
    meal_count: number
    scenario: string
  }
  target_audience?: string
  budget_range?: [number, number]
  special_requirements?: string[]
}

// ==================== 营养师输出 ====================

export interface NutritionPlan {
  calories: number
  protein: number
  fat: number
  carbohydrates: number
  fiber: number
  sodium: number
  vitamins: Record<string, number>
  minerals: Record<string, number>
}

export interface IngredientStructure {
  ingredient_id: string
  name: string
  category: string
  quantity: number
  nutrition_contribution: number
}

export interface NutritionistOutput {
  nutrition_plan: NutritionPlan
  ingredient_structures: IngredientStructure[]
  nutrition_notes: string[]
  warnings: string[]
}

// ==================== 研发主厨输出 ====================

export interface ConceptCard {
  dish_name: string
  food_combination: Array<{
    name: string
    quantity: number
    unit: string
  }>
  flavor_structure: Record<string, unknown>
  plating_direction: string
  estimated_cost: number
  nutrition_direction: string
  cooking_method: string
  innovation_points: string[]
  reference_images?: string[]
}

export interface GroupMealPlan {
  menu_items: ConceptCard[]
  total_cost: number
  serving_size: number
  meal_count: number
  preparation_timeline: Array<{
    task: string
    duration: number
  }>
}

export interface RDChefOutput {
  concept_card?: ConceptCard
  group_meal_plan?: GroupMealPlan
  design_notes: string[]
  alternatives: Record<string, unknown>[]
}

// ==================== 厨师长输出 ====================

export interface RecipeStep {
  step_number: number
  description: string
  duration: number
  temperature?: string
  tips?: string
}

export interface StandardRecipeCard {
  recipe_id: string
  dish_name: string
  version: string
  ingredients: Array<{
    name: string
    quantity: number
    unit: string
  }>
  seasonings: Array<{
    name: string
    quantity: number
    unit: string
  }>
  equipment: string[]
  steps: RecipeStep[]
  quality_standards: string[]
  plating_specification: string
  shelf_life: string
  cost_breakdown: Record<string, number>
  nutrition_facts: Record<string, number>
  review_status: string
  reviewed_by?: string
  review_comments?: string
  created_at: string
}

export interface HeadChefOutput {
  recipe_card: StandardRecipeCard
  review_notes: string[]
}

// ==================== 工作流相关 ====================

export interface WorkflowContext {
  workflow_id: string
  status: WorkflowStatus
  customer_input: string
  director_output?: OperationsDirectorOutput
  nutritionist_output?: NutritionistOutput
  rd_chef_output?: RDChefOutput
  head_chef_output?: HeadChefOutput
  approval_status?: string
  approval_comments?: string
  approved_by?: string
  revision_count: number
  max_revisions: number
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

// ==================== WebSocket 消息 ====================

export type WSMessageType =
  | 'connection_established'
  | 'agent_status_change'
  | 'step_completed'
  | 'approval_required'
  | 'workflow_completed'
  | 'workflow_failed'
  | 'error'

export interface WSMessage {
  type: WSMessageType
  workflow_id: string
  timestamp: string
  data: Record<string, unknown>
}

// ==================== API 请求/响应 ====================

export interface CreateWorkflowRequest {
  customer_input: string
  model?: string
  metadata?: Record<string, unknown>
}

export interface ApprovalRequest {
  approved: boolean
  comments: string
  reviewer: string
}

export interface WorkflowResponse {
  workflow_id: string
  status: string
  customer_input: string
  created_at: string
  updated_at: string
}

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data?: T
}

// ==================== 审批相关 ====================

export interface Approval {
  id: string
  workflow_id: string
  step_id?: string
  status: string
  comments: string
  reviewer: string
  reviewed_at: string
}
