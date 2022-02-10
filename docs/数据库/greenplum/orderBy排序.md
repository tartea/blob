```sql
SELECT
   * 
FROM
   (
   SELECT
      S_0.respondent_id AS respondent_id,
      S_0.respondent_id_of_superior_legal_person AS respondent_id_of_superior_legal_person,
      S_0.respondent_scale AS respondent_scale,
      S_0.respondent_caption AS respondent_caption ,
      period_id
   FROM
      t_2011_ytbcq2020_record S_0 
   WHERE period_id='20210040'
   ) AS tmp 
      ORDER BY
      respondent_id desc 
   LIMIT 20 OFFSET 0
```

```sql
 SELECT
	* 
FROM
	(
	SELECT
		S_0.respondent_id AS respondent_id,
		S_0.respondent_id_of_superior_legal_person AS respondent_id_of_superior_legal_person,
		S_0.respondent_scale AS respondent_scale,
		S_0.respondent_caption AS respondent_caption ,
		period_id
	FROM
		t_2011_ytbcq2020_record S_0 
	ORDER BY
		respondent_id desc 
	) AS tmp 
		WHERE period_id='20210040'
	LIMIT 20 OFFSET 0
```

从sql的语法上来讲，上面两条sql语句的结果应该是一样的，但是实际查询的结果是不一样的
这是因为postgres虽然支持在自查询中添加排序，语法上是支持的，但是在实际执行中，排序部分的代码是不会执行的  

可以使用**explain**命令去查看两条语句的解释步骤，会发现下面的步骤中没有sort解释步骤

<img src="https://gitee.com/gluten/images/raw/master/images/202111131454019.png" alt="image-20211025112303881" style="zoom:50%;" />

<img src="https://gitee.com/gluten/images/raw/master/images/202111131454264.png" alt="image-20211025112341547" style="zoom:50%;" />  

所以在实际编写sql语句的过程中，一定要将order by写在最外层

