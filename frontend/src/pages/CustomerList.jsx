import { useState, useEffect, useCallback, useRef } from 'react'
import CustomerTable from '../components/CustomerTable'
import CustomerForm from '../components/CustomerForm'
import { Modal } from '../components/ui/Modal'
import { Input, Select } from '../components/ui/FormControls'
import { getCustomers, createCustomer } from '../api'

const COUNTRY_OPTIONS = [
  { value: 'France', label: 'France' },
  { value: 'Germany', label: 'Germany' },
  { value: 'UK', label: 'UK' },
  { value: 'USA', label: 'USA' },
  { value: 'Japan', label: 'Japan' },
  { value: 'UAE', label: 'UAE' },
  { value: 'Australia', label: 'Australia' },
  { value: 'Russia', label: 'Russia' },
  { value: 'Italy', label: 'Italy' },
  { value: 'Spain', label: 'Spain' },
  { value: 'Switzerland', label: 'Switzerland' },
  { value: 'Netherlands', label: 'Netherlands' },
]

const TYPE_OPTIONS = [
  { value: '进口商', label: '进口商' },
  { value: '批发商', label: '批发商' },
  { value: '品牌商', label: '品牌商' },
  { value: '米其林餐厅', label: '米其林餐厅' },
  { value: '高端酒店', label: '高端酒店' },
  { value: '零售商', label: '零售商' },
]

const GRADE_OPTIONS = [
  { value: 'A', label: 'A级 (80+)' },
  { value: 'B', label: 'B级 (60-79)' },
  { value: 'C', label: 'C级 (40-59)' },
  { value: 'D', label: 'D级 (<40)' },
]

const STATUS_OPTIONS = [
  { value: 'NEW', label: '新客户' },
  { value: 'CONTACTED', label: '已联系' },
  { value: 'NEGOTIATING', label: '谈判中' },
  { value: 'WON', label: '已成交' },
  { value: 'LOST', label: '已流失' },
  { value: 'INACTIVE', label: '已搁置' },
]

export default function CustomerList() {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [filters, setFilters] = useState({
    country: '',
    customer_type: '',
    grade: '',
    follow_status: '',
  })
  const [searchInput, setSearchInput] = useState('')
  const [sort, setSort] = useState({ field: 'updated_at', dir: 'desc' })
  // 静默刷新（后台刷新，不显示 loading 遮罩）
  const [refreshing, setRefreshing] = useState(false)
  // 搜索刚完成时立即刷新（通知来自 SearchPage）
  const justImported = useRef(false)

  const fetchCustomers = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    try {
      const params = { ...filters }
      if (sort.field) {
        params.sort_by = sort.field
        params.sort_dir = sort.dir
      }
      if (searchInput.trim()) {
        if (/^[\d\.]+$/.test(searchInput.trim())) {
          params.hs_code = searchInput.trim()
        } else {
          params.product_name = searchInput.trim()
        }
      }
      const res = await getCustomers(params)
      setCustomers(res.data?.items || [])
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [filters, sort, searchInput])

  // 首次加载
  useEffect(() => {
    fetchCustomers()
  }, [fetchCustomers])

  // 每 10 秒静默刷新（搜索导入的新客户实时出现在列表中）
  useEffect(() => {
    const interval = setInterval(() => {
      // 有筛选条件时跳过静默刷新，避免干扰用户筛选
      const hasFilters = filters.country || filters.customer_type || filters.grade || filters.follow_status || searchInput.trim()
      if (!hasFilters) {
        fetchCustomers(true)
      }
    }, 10000)
    return () => clearInterval(interval)
  }, [fetchCustomers, filters, searchInput])

  const handleSort = (field) => {
    setSort((prev) => ({
      field,
      dir: prev.field === field && prev.dir === 'asc' ? 'desc' : 'asc',
    }))
  }

  const handleCreate = async (data) => {
    setFormLoading(true)
    try {
      await createCustomer(data)
      setShowForm(false)
      fetchCustomers()
    } catch (err) {
      alert('创建失败: ' + err.message)
    } finally {
      setFormLoading(false)
    }
  }

  const hasActiveFilters = !!(filters.country || filters.customer_type || filters.grade || filters.follow_status || searchInput)

  return (
    <div className="space-y-4">
      {/* 静默刷新指示 */}
      {refreshing && (
        <div className="text-[11px] text-caviar-muted flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          同步中...
        </div>
      )}
      {/* 顶部操作栏 */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* 搜索 + 筛选 */}
        <div className="flex flex-wrap gap-2 items-center">
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="搜索产品 / HS CODE"
            size="sm"
            containerClassName="w-52"
            suffix={searchInput ? (
              <button
                onClick={() => setSearchInput('')}
                className="text-text-muted hover:text-text-secondary transition-colors leading-none text-[14px]"
              >
                ×
              </button>
            ) : null}
          />
          {[
            { name: 'country',        options: COUNTRY_OPTIONS,  placeholder: '国家' },
            { name: 'customer_type', options: TYPE_OPTIONS,     placeholder: '类型' },
            { name: 'grade',         options: GRADE_OPTIONS,     placeholder: '等级' },
            { name: 'follow_status', options: STATUS_OPTIONS,    placeholder: '状态' },
          ].map((f) => (
            <Select
              key={f.name}
              options={f.options}
              value={filters[f.name]}
              onChange={(e) => setFilters({ ...filters, [f.name]: e.target.value })}
              placeholder={f.placeholder}
              containerClassName="w-32"
            />
          ))}
          {hasActiveFilters && (
            <button
              onClick={() => {
                setFilters({ country: '', customer_type: '', grade: '', follow_status: '' })
                setSearchInput('')
              }}
              className="text-[12px] text-accent hover:opacity-75 transition-opacity"
            >
              清除
            </button>
          )}
        </div>

        <button onClick={() => setShowForm(true)} className="btn btn-primary btn-sm shadow-sm">
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
          </svg>
          新增客户
        </button>
      </div>

      {/* 表格 */}
      <div className="card overflow-hidden">
        <CustomerTable
          customers={customers}
          loading={loading}
          onSort={handleSort}
          sortField={sort.field}
          sortDir={sort.dir}
        />
      </div>

      {/* 新增客户弹窗 */}
      <Modal
        open={showForm}
        title="新增客户"
        size="lg"
        onClose={() => setShowForm(false)}
      >
        {showForm && (
          <CustomerForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            loading={formLoading}
          />
        )}
      </Modal>
    </div>
  )
}
