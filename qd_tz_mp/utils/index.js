import reg from '@/constant/regular.js'

// 正则校验
export function verifyField(regName, val) {
	return reg[regName].test(val)
}