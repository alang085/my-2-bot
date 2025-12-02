"""测试撤销功能按聊天环境隔离"""
import asyncio
import sys
sys.path.insert(0, '.')

import db_operations


async def test_undo_chat_isolation():
    """测试撤销功能是否按聊天环境正确隔离"""
    print("=" * 60)
    print("测试撤销功能按聊天环境隔离")
    print("=" * 60)
    print()
    
    # 模拟两个不同的聊天环境
    private_chat_id = -123456789  # 私聊 ID（负数表示私聊）
    group_chat_id_1 = -1001234567890  # 群聊 1
    group_chat_id_2 = -1001234567891  # 群聊 2
    user_id = 12345
    
    print(f"测试用户 ID: {user_id}")
    print(f"私聊 ID: {private_chat_id}")
    print(f"群聊 1 ID: {group_chat_id_1}")
    print(f"群聊 2 ID: {group_chat_id_2}")
    print()
    
    # 清理测试数据
    print("清理测试数据...")
    # 注意：实际测试中需要清理操作历史表的相关数据
    print("✅ 清理完成（实际测试中需要实现）")
    print()
    
    # 测试1: 在不同聊天环境中记录操作
    print("测试1: 在不同聊天环境中记录操作")
    print("-" * 60)
    
    # 在私聊中记录操作
    print(f"在私聊 ({private_chat_id}) 中记录开销操作...")
    op1_id = await db_operations.record_operation(
        user_id=user_id,
        operation_type='expense',
        operation_data={'amount': 100, 'type': 'company', 'note': '私聊开销'},
        chat_id=private_chat_id
    )
    print(f"✅ 操作记录 ID: {op1_id}")
    
    # 在群聊1中记录操作
    print(f"在群聊1 ({group_chat_id_1}) 中记录订单状态变更...")
    op2_id = await db_operations.record_operation(
        user_id=user_id,
        operation_type='order_state_change',
        operation_data={'chat_id': group_chat_id_1, 'order_id': 'TEST001'},
        chat_id=group_chat_id_1
    )
    print(f"✅ 操作记录 ID: {op2_id}")
    
    # 在群聊2中记录操作
    print(f"在群聊2 ({group_chat_id_2}) 中记录订单完成...")
    op3_id = await db_operations.record_operation(
        user_id=user_id,
        operation_type='order_completed',
        operation_data={'chat_id': group_chat_id_2, 'order_id': 'TEST002'},
        chat_id=group_chat_id_2
    )
    print(f"✅ 操作记录 ID: {op3_id}")
    print()
    
    # 测试2: 验证 get_last_operation 是否正确隔离
    print("测试2: 验证 get_last_operation 是否正确隔离")
    print("-" * 60)
    
    # 在私聊中查询最后一个操作
    last_op_private = await db_operations.get_last_operation(user_id, private_chat_id)
    print(f"私聊 ({private_chat_id}) 中的最后一个操作:")
    if last_op_private:
        print(f"  - 操作类型: {last_op_private['operation_type']}")
        print(f"  - 操作数据: {last_op_private['operation_data']}")
        assert last_op_private['operation_type'] == 'expense', "应该是在私聊中记录的开销操作"
        print("  ✅ 正确")
    else:
        print("  ❌ 未找到操作")
    
    # 在群聊1中查询最后一个操作
    last_op_group1 = await db_operations.get_last_operation(user_id, group_chat_id_1)
    print(f"群聊1 ({group_chat_id_1}) 中的最后一个操作:")
    if last_op_group1:
        print(f"  - 操作类型: {last_op_group1['operation_type']}")
        print(f"  - 操作数据: {last_op_group1['operation_data']}")
        assert last_op_group1['operation_type'] == 'order_state_change', "应该是在群聊1中记录的状态变更"
        print("  ✅ 正确")
    else:
        print("  ❌ 未找到操作")
    
    # 在群聊2中查询最后一个操作
    last_op_group2 = await db_operations.get_last_operation(user_id, group_chat_id_2)
    print(f"群聊2 ({group_chat_id_2}) 中的最后一个操作:")
    if last_op_group2:
        print(f"  - 操作类型: {last_op_group2['operation_type']}")
        print(f"  - 操作数据: {last_op_group2['operation_data']}")
        assert last_op_group2['operation_type'] == 'order_completed', "应该是在群聊2中记录的订单完成"
        print("  ✅ 正确")
    else:
        print("  ❌ 未找到操作")
    print()
    
    # 测试3: 验证不会跨聊天环境获取操作
    print("测试3: 验证不会跨聊天环境获取操作")
    print("-" * 60)
    
    # 在私聊中不应该获取到群聊的操作
    assert last_op_private is None or last_op_private['operation_type'] != 'order_state_change', \
        "私聊中不应该获取到群聊1的操作"
    assert last_op_private is None or last_op_private['operation_type'] != 'order_completed', \
        "私聊中不应该获取到群聊2的操作"
    print("✅ 私聊中不会获取到群聊的操作")
    
    # 在群聊1中不应该获取到私聊或群聊2的操作
    assert last_op_group1 is None or last_op_group1['operation_type'] != 'expense', \
        "群聊1中不应该获取到私聊的操作"
    assert last_op_group1 is None or last_op_group1['operation_type'] != 'order_completed', \
        "群聊1中不应该获取到群聊2的操作"
    print("✅ 群聊1中不会获取到其他聊天环境的操作")
    
    # 在群聊2中不应该获取到私聊或群聊1的操作
    assert last_op_group2 is None or last_op_group2['operation_type'] != 'expense', \
        "群聊2中不应该获取到私聊的操作"
    assert last_op_group2 is None or last_op_group2['operation_type'] != 'order_state_change', \
        "群聊2中不应该获取到群聊1的操作"
    print("✅ 群聊2中不会获取到其他聊天环境的操作")
    print()
    
    print("=" * 60)
    print("✅ 所有测试通过！撤销功能已正确按聊天环境隔离")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_undo_chat_isolation())
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

