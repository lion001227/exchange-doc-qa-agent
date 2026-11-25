create table  if not exists `users`(
    id bigint not null auto_increment comment '用户ID',
    username varchar(50) not null comment '用户名',
    email varchar(100) unique not null comment '邮箱',
    password varchar(255) not null comment '密码',
    created_at datetime default current_timestamp comment '注册时间',
    updated_at datetime default current_timestamp on update current_timestamp comment '更新时间',
    primary key (id)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

create table if not exists `conversations`(
    id bigint  not null auto_increment comment '会话ID',
    user_id bigint not null comment '用户ID',
    thread_id varchar(100) not null comment 'LangGraph会话ID',
    title varchar(200) null comment '会话标题',
    created_at datetime default current_timestamp comment '创建时间',
    updated_at datetime default current_timestamp on update current_timestamp comment '最后更新时间',
    primary key (id),
    unique index `uk_thread` (`thread_id`),
    key `idx_created`(`created_at`),
    constraint `fk_user_id`
        foreign key (`user_id`)
        references `users`(`id`)
        on delete cascade
        on update cascade

)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表';

create table if not exists `messages`(
    id bigint not null auto_increment comment '消息ID',
    conversation_id bigint not null comment '会话所属ID',
    user_id bigint not null comment '用户id',
    role varchar(20) not null comment '角色',
    content text null comment '消息内容',
    metadata json null comment '来源，工具调用等附加信息',
    tool_call varchar(50) null comment '工具调用',
    relevant_document text null comment  '相关文档',
    input_token_usage int null comment '输入token消耗量',
    output_token_usage int null comment '输出token消耗量',
    total_token_usage int null comment '总token消耗量',
    latency float null comment '响应耗时',
    created_at datetime default current_timestamp comment '消息创建时间',
    primary key (id),
    key `idx_conv_created`(`conversation_id`,`created_at`),
    key `idx_created_at`(`created_at`),
    constraint `chk_role` check  (`role` in ('assistant','user','tool','system')),
    constraint `fk_conversation`
        foreign key (conversation_id)
        references  `conversations`(`id`)
        on delete cascade
        on UPDATE cascade,
    constraint `fk_user`
    foreign key (user_id) references `users`(id)
    on delete cascade
    on update cascade
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

