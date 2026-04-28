import { useState } from 'react'
import { Input, Textarea, Select } from './ui/FormControls'

const customerTypes = [
  { value: '进口商', label: '进口商' },
  { value: '批发商', label: '批发商' },
  { value: '品牌商', label: '品牌商' },
  { value: '米其林餐厅', label: '米其林餐厅' },
  { value: '高端酒店', label: '高端酒店' },
  { value: '零售商', label: '零售商' },
  { value: '其他', label: '其他' },
]

const countries = [
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
  { value: '其他', label: '其他' },
]

const socialMediaFields = [
  { key: 'facebook',  label: 'Facebook',   placeholder: '粉丝页ID或链接' },
  { key: 'instagram', label: 'Instagram',  placeholder: '账号ID' },
  { key: 'twitter',   label: 'Twitter/X',  placeholder: '账号ID' },
  { key: 'youtube',   label: 'YouTube',    placeholder: '频道ID或链接' },
  { key: 'tiktok',    label: 'TikTok',     placeholder: '账号ID' },
  { key: 'whatsapp',  label: 'WhatsApp',   placeholder: '号码' },
]

const PRIORITY_OPTIONS = [
  { value: 'HIGH',   label: '高优先级' },
  { value: 'MEDIUM', label: '中优先级' },
  { value: 'LOW',    label: '低优先级' },
]

export default function CustomerForm({ initialData, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(initialData || {
    company_name_en: '',
    company_name_local: '',
    country: '',
    city: '',
    contact_name: '',
    email: '',
    phone: '',
    linkedin_url: '',
    website: '',
    address: '',
    notes: '',
    priority_level: 'MEDIUM',
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      company_name_en: form.company_name_en,
      company_name_local: form.company_name_local,
      contact_name: form.contact_name,
      email: form.email,
      phone: form.phone,
      linkedin_url: form.linkedin_url,
      website: form.website,
      address: form.address,
      notes: form.notes,
      priority_level: form.priority_level,
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* 基本信息 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="公司名称（英文） *"
          name="company_name_en"
          value={form.company_name_en}
          onChange={handleChange}
          required
          placeholder="例: Maison Petrossian"
        />
        <Input
          label="公司名称（本地）"
          name="company_name_local"
          value={form.company_name_local}
          onChange={handleChange}
          placeholder="本地语言公司名"
        />
        <Select
          label="国家 *"
          name="country"
          options={countries}
          value={form.country}
          onChange={handleChange}
          required
          placeholder="选择国家"
        />
        <Input
          label="城市"
          name="city"
          value={form.city}
          onChange={handleChange}
          placeholder="城市"
        />
      </div>

      {/* 联系方式 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="决策人 / 联系人"
          name="contact_name"
          value={form.contact_name}
          onChange={handleChange}
          placeholder="如: Mr. Alexandre Dupont"
        />
        <Input
          label="邮箱"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          placeholder="contact@company.com"
        />
        <Input
          label="电话"
          name="phone"
          value={form.phone}
          onChange={handleChange}
          placeholder="+33 1 23 45 67 89"
        />
        <Input
          label="官网"
          name="website"
          value={form.website}
          onChange={handleChange}
          placeholder="https://www.company.com"
        />
      </div>

      {/* 领英 + 客户类型 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="领英主页链接"
          name="linkedin_url"
          value={form.linkedin_url}
          onChange={handleChange}
          placeholder="https://linkedin.com/in/..."
        />
        <Select
          label="客户类型"
          name="customer_type"
          options={customerTypes}
          value={form.customer_type}
          onChange={handleChange}
          placeholder="选择类型"
        />
      </div>

      <Input
        label="公司地址"
        name="address"
        value={form.address}
        onChange={handleChange}
        placeholder="详细地址"
      />

      {/* 优先级 */}
      <Select
        label="优先级"
        name="priority_level"
        options={PRIORITY_OPTIONS}
        value={form.priority_level}
        onChange={handleChange}
      />

      {/* 备注 */}
      <Textarea
        label="备注"
        name="notes"
        value={form.notes}
        onChange={handleChange}
        rows={3}
        placeholder="备注信息..."
      />

      {/* 提交按钮 */}
      <div className="flex justify-end gap-2.5 pt-3 border-t border-border-subtle">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn btn-secondary btn-sm">
            取消
          </button>
        )}
        <button type="submit" disabled={loading} className="btn btn-primary btn-sm shadow-sm">
          {loading ? '保存中...' : '保存'}
        </button>
      </div>
    </form>
  )
}
