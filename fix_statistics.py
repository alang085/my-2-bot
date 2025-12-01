"""修复统计数据：根据实际订单数据重新计算所有统计数据"""
import asyncio
import sys
import db_operations

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def fix_statistics():
    """根据实际订单数据重新计算并修复所有统计数据"""
    print("=" * 60)
    print("修复统计数据")
    print("=" * 60)
    
    # 1. 获取所有归属ID（从 orders 表）
    all_orders = await db_operations.search_orders_advanced_all_states({})
    all_group_ids = list(set(order.get('group_id') for order in all_orders if order.get('group_id')))
    
    print(f"\n从订单表找到 {len(all_group_ids)} 个归属ID: {', '.join(sorted(all_group_ids))}")
    
    # 2. 对每个归属ID，重新计算统计数据
    for group_id in sorted(all_group_ids):
        print(f"\n{'=' * 60}")
        print(f"处理归属ID: {group_id}")
        print(f"{'=' * 60}")
        
        # 从 orders 表查询实际订单
        group_orders = [o for o in all_orders if o.get('group_id') == group_id]
        
        # 按状态分类统计
        valid_orders = [o for o in group_orders if o.get('state') in ['normal', 'overdue']]
        breach_orders = [o for o in group_orders if o.get('state') == 'breach']
        completed_orders = [o for o in group_orders if o.get('state') == 'end']
        breach_end_orders = [o for o in group_orders if o.get('state') == 'breach_end']
        
        # 计算实际统计数据
        actual_valid_count = len(valid_orders)
        actual_valid_amount = sum(o.get('amount', 0) for o in valid_orders)
        actual_breach_count = len(breach_orders)
        actual_breach_amount = sum(o.get('amount', 0) for o in breach_orders)
        actual_completed_count = len(completed_orders)
        actual_completed_amount = sum(o.get('amount', 0) for o in completed_orders)
        actual_breach_end_count = len(breach_end_orders)
        actual_breach_end_amount = sum(o.get('amount', 0) for o in breach_end_orders)
        
        print(f"\n实际订单数据：")
        print(f"  有效订单: {actual_valid_count} 个, {actual_valid_amount:,.2f}")
        print(f"  违约订单: {actual_breach_count} 个, {actual_breach_amount:,.2f}")
        print(f"  完成订单: {actual_completed_count} 个, {actual_completed_amount:,.2f}")
        print(f"  违约完成: {actual_breach_end_count} 个, {actual_breach_end_amount:,.2f}")
        
        # 获取当前统计表数据
        grouped_data = await db_operations.get_grouped_data(group_id)
        print(f"\n当前统计表数据：")
        print(f"  有效订单: {grouped_data['valid_orders']} 个, {grouped_data['valid_amount']:,.2f}")
        print(f"  违约订单: {grouped_data['breach_orders']} 个, {grouped_data['breach_amount']:,.2f}")
        print(f"  完成订单: {grouped_data['completed_orders']} 个, {grouped_data['completed_amount']:,.2f}")
        print(f"  违约完成: {grouped_data['breach_end_orders']} 个, {grouped_data['breach_end_amount']:,.2f}")
        
        # 计算差异并修复
        async def fix_field(field_name, actual_count, actual_amount, current_count, current_amount):
            count_diff = actual_count - current_count
            amount_diff = actual_amount - current_amount
            
            if abs(count_diff) > 0 or abs(amount_diff) > 0.01:
                print(f"\n修复 {field_name} 统计：")
                if count_diff != 0:
                    await db_operations.update_grouped_data(group_id, f'{field_name}_orders', count_diff)
                    print(f"  调整订单数: {count_diff}")
                if abs(amount_diff) > 0.01:
                    await db_operations.update_grouped_data(group_id, f'{field_name}_amount', amount_diff)
                    print(f"  调整金额: {amount_diff:,.2f}")
                return True
            return False
        
        fixed = False
        fixed |= await fix_field('valid', actual_valid_count, actual_valid_amount, 
                          grouped_data['valid_orders'], grouped_data['valid_amount'])
        fixed |= await fix_field('breach', actual_breach_count, actual_breach_amount,
                          grouped_data['breach_orders'], grouped_data['breach_amount'])
        fixed |= await fix_field('completed', actual_completed_count, actual_completed_amount,
                          grouped_data['completed_orders'], grouped_data['completed_amount'])
        fixed |= await fix_field('breach_end', actual_breach_end_count, actual_breach_end_amount,
                          grouped_data['breach_end_orders'], grouped_data['breach_end_amount'])
        
        if not fixed:
            print(f"\n✅ 数据一致，无需修复")
        else:
            # 验证修复结果
            grouped_data_after = await db_operations.get_grouped_data(group_id)
            print(f"\n验证修复结果：")
            print(f"  有效订单: {grouped_data_after['valid_orders']} (实际: {actual_valid_count})")
            print(f"  有效金额: {grouped_data_after['valid_amount']:,.2f} (实际: {actual_valid_amount:,.2f})")
            
            if (grouped_data_after['valid_orders'] == actual_valid_count and 
                abs(grouped_data_after['valid_amount'] - actual_valid_amount) < 0.01):
                print(f"  ✅ 修复成功！")
            else:
                print(f"  ⚠️ 仍有差异，请检查。")
    
    # 3. 修复全局统计数据
    print(f"\n{'=' * 60}")
    print(f"修复全局统计数据")
    print(f"{'=' * 60}")
    
    # 按状态分类统计所有订单
    all_valid_orders = [o for o in all_orders if o.get('state') in ['normal', 'overdue']]
    all_breach_orders = [o for o in all_orders if o.get('state') == 'breach']
    all_completed_orders = [o for o in all_orders if o.get('state') == 'end']
    all_breach_end_orders = [o for o in all_orders if o.get('state') == 'breach_end']
    
    global_valid_count = len(all_valid_orders)
    global_valid_amount = sum(o.get('amount', 0) for o in all_valid_orders)
    global_breach_count = len(all_breach_orders)
    global_breach_amount = sum(o.get('amount', 0) for o in all_breach_orders)
    global_completed_count = len(all_completed_orders)
    global_completed_amount = sum(o.get('amount', 0) for o in all_completed_orders)
    global_breach_end_count = len(all_breach_end_orders)
    global_breach_end_amount = sum(o.get('amount', 0) for o in all_breach_end_orders)
    
    financial_data = await db_operations.get_financial_data()
    
    print(f"\n实际全局数据：")
    print(f"  有效订单: {global_valid_count} 个, {global_valid_amount:,.2f}")
    print(f"  违约订单: {global_breach_count} 个, {global_breach_amount:,.2f}")
    print(f"  完成订单: {global_completed_count} 个, {global_completed_amount:,.2f}")
    print(f"  违约完成: {global_breach_end_count} 个, {global_breach_end_amount:,.2f}")
    
    print(f"\n当前统计表数据：")
    print(f"  有效订单: {financial_data['valid_orders']} 个, {financial_data['valid_amount']:,.2f}")
    print(f"  违约订单: {financial_data['breach_orders']} 个, {financial_data['breach_amount']:,.2f}")
    print(f"  完成订单: {financial_data['completed_orders']} 个, {financial_data['completed_amount']:,.2f}")
    print(f"  违约完成: {financial_data['breach_end_orders']} 个, {financial_data['breach_end_amount']:,.2f}")
    
    # 修复全局统计
    async def fix_global_field(field_name, actual_count, actual_amount, current_count, current_amount):
        count_diff = actual_count - current_count
        amount_diff = actual_amount - current_amount
        
        if abs(count_diff) > 0 or abs(amount_diff) > 0.01:
            print(f"\n修复全局 {field_name} 统计：")
            if count_diff != 0:
                await db_operations.update_financial_data(f'{field_name}_orders', count_diff)
                print(f"  调整订单数: {count_diff}")
            if abs(amount_diff) > 0.01:
                await db_operations.update_financial_data(f'{field_name}_amount', amount_diff)
                print(f"  调整金额: {amount_diff:,.2f}")
            return True
        return False
    
    fixed = False
    fixed |= await fix_global_field('valid', global_valid_count, global_valid_amount,
                              financial_data['valid_orders'], financial_data['valid_amount'])
    fixed |= await fix_global_field('breach', global_breach_count, global_breach_amount,
                              financial_data['breach_orders'], financial_data['breach_amount'])
    fixed |= await fix_global_field('completed', global_completed_count, global_completed_amount,
                              financial_data['completed_orders'], financial_data['completed_amount'])
    fixed |= await fix_global_field('breach_end', global_breach_end_count, global_breach_end_amount,
                              financial_data['breach_end_orders'], financial_data['breach_end_amount'])
    
    if not fixed:
        print(f"\n✅ 全局数据一致，无需修复")
    else:
        print(f"\n✅ 全局统计数据修复完成！")
    
    print(f"\n{'=' * 60}")
    print(f"修复完成！")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    asyncio.run(fix_statistics())

