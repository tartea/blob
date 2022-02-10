今天看到一个问题，在**greenplum**中一个schema中存在一张表数据表的时候，使用hibernate在另外一个schema中发现不能默认创建相同的表。

看到这个问题的时候觉得很奇怪，因为如果当前数据库中不存在这张表的的时候就是可以创建的，但是只要有一个schema中存在这张表的时候，在另外的schema中就不能创建，按理说不同的schema中是可以创建相同的表的。

这个问题可以从两个方面来分析：

1. hibernate不支持在不同的schema中创建相同的表
2. 参数配置错误

#### 分析

既然数据库不存在的时候可以创建表，那么就这个创建表这个方法开始，往前面找，找到方法（判断表存在就不创建表）就停止。

因为控制台输出**Hibernate:  create table ......**

```java
public class SqlStatementLogger {
	/**
	 * Log a SQL statement string using the specified formatter
	 *
	 * @param statement The SQL statement.
	 * @param formatter The formatter to use.
	 */
	public void logStatement(String statement, Formatter formatter) {
		if ( format ) {
			if ( logToStdout || LOG.isDebugEnabled() ) {
				statement = formatter.format( statement );
			}
		}
		LOG.debug( statement );
		if ( logToStdout ) {
			System.out.println( "Hibernate: " + statement );
		}
	}
}
```

打断点，启动程序，从栈帧中到前面的方法。

<img src="https://gitee.com/gluten/images/raw/master/images/202111131451720.png" alt="image-20211019212126470" style="zoom:40%;" />

```java
public class GroupedSchemaMigratorImpl{
  
	@Override
	protected NameSpaceTablesInformation performTablesMigration(
			Metadata metadata,
			DatabaseInformation existingDatabase,
			ExecutionOptions options,
			Dialect dialect,
			Formatter formatter,
			Set<String> exportIdentifiers,
			boolean tryToCreateCatalogs,
			boolean tryToCreateSchemas,
			Set<Identifier> exportedCatalogs,
			Namespace namespace, GenerationTarget[] targets) {
		final NameSpaceTablesInformation tablesInformation =
				new NameSpaceTablesInformation( metadata.getDatabase().getJdbcEnvironment().getIdentifierHelper() );

		if ( schemaFilter.includeNamespace( namespace ) ) {
			createSchemaAndCatalog(
					existingDatabase,
					options,
					dialect,
					formatter,
					tryToCreateCatalogs,
					tryToCreateSchemas,
					exportedCatalogs,
					namespace,
					targets
			);
      //通过过滤从数据库中获取表
			final NameSpaceTablesInformation tables = existingDatabase.getTablesInformation( namespace );
			for ( Table table : namespace.getTables() ) {
				if ( schemaFilter.includeTable( table ) && table.isPhysicalTable() ) {
					checkExportIdentifier( table, exportIdentifiers );
					final TableInformation tableInformation = tables.getTableInformation( table );
					if ( tableInformation == null ) {
            //创建表
						createTable( table, dialect, metadata, formatter, options, targets );
					}
					else if ( tableInformation != null && tableInformation.isPhysicalTable() ) {
						tablesInformation.addTableInformation( tableInformation );
						migrateTable( table, tableInformation, dialect, metadata, formatter, options, targets );
					}
				}
			}

			for ( Table table : namespace.getTables() ) {
				if ( schemaFilter.includeTable( table ) && table.isPhysicalTable() ) {
					final TableInformation tableInformation = tablesInformation.getTableInformation( table );
					if ( tableInformation == null || ( tableInformation != null && tableInformation.isPhysicalTable() ) ) {
						applyIndexes( table, tableInformation, dialect, metadata, formatter, options, targets );
						applyUniqueKeys( table, tableInformation, dialect, metadata, formatter, options, targets );
					}
				}
			}
		}
		return tablesInformation;
	}

}
```

从上面的图可以看到一个方法是从数据库中查找数据库的。

```java
@Override
public NameSpaceTablesInformation getTablesInformation(Namespace namespace) {
		return extractor.getTables( namespace.getPhysicalName().getCatalog(), namespace.getPhysicalName().getSchema() );
	}

public NameSpaceTablesInformation getTables(Identifier catalog, Identifier schema) {

		String catalogFilter = null;
		String schemaFilter = null;

		if ( extractionContext.getJdbcEnvironment().getNameQualifierSupport().supportsCatalogs() ) {
			if ( catalog == null ) {
				if ( extractionContext.getJdbcEnvironment().getCurrentCatalog() != null ) {
					// 1) look in current namespace
					catalogFilter = toMetaDataObjectName( extractionContext.getJdbcEnvironment().getCurrentCatalog() );
				}
				else if ( extractionContext.getDefaultCatalog() != null ) {
					// 2) look in default namespace
					catalogFilter = toMetaDataObjectName( extractionContext.getDefaultCatalog() );
				}
				else {
					catalogFilter = "";
				}
			}
			else {
				catalogFilter = toMetaDataObjectName( catalog );
			}
		}
		//如果支持schema，如果设置了schema，那么从环境中取，如果没有那么为空。
  	//可以看出来，如果schemaFilter为空字符串，那么相当于获取所有schema中的表
		if ( extractionContext.getJdbcEnvironment().getNameQualifierSupport().supportsSchemas() ) {
			if ( schema == null ) {
				if ( extractionContext.getJdbcEnvironment().getCurrentSchema() != null ) {
					// 1) look in current namespace
					schemaFilter = toMetaDataObjectName( extractionContext.getJdbcEnvironment().getCurrentSchema() );
				}
				else if ( extractionContext.getDefaultSchema() != null ) {
					// 2) look in default namespace
					schemaFilter = toMetaDataObjectName( extractionContext.getDefaultSchema() );
				}
				else {
					schemaFilter = "";
				}
			}
			else {
				schemaFilter = toMetaDataObjectName( schema );
			}
		}

		try {
			ResultSet resultSet = extractionContext.getJdbcDatabaseMetaData().getTables(
					catalogFilter,
					schemaFilter,
					"%",
					tableTypes
			);

			final NameSpaceTablesInformation tablesInformation = processTableResults( resultSet );
			populateTablesWithColumns( catalogFilter, schemaFilter, tablesInformation );
			return tablesInformation;
		}
		catch (SQLException sqlException) {
			throw convertSQLException( sqlException, "Error accessing table metadata" );
		}
	}
```

从上面的代码中可以看出来，只要配置了**currentSchema**，那么是可以在不同的schema中生成相同表的。

所以需要查看**currentSchema**是在什么时候设置参数的。

**JdbcEnvironment**该方法是一个接口，只有**getCurrentSchema**，查找它的实现，会发现只有一个实现**JdbcEnvironmentImpl**，从构造函数中可以发现如下代码

```java
this.currentSchema = Identifier.toIdentifier(
				cfgService.getSetting( AvailableSettings.DEFAULT_SCHEMA, StandardConverters.STRING )
		);
```

这里就可以清楚的知道，常量**DEFAULT_SCHEMA**就是需要设置的参数。

```java
	/**
	 * A default database schema (owner) name to use for unqualified tablenames
	 *
	 * @see MetadataBuilder#applyImplicitSchemaName
	 */
	String DEFAULT_SCHEMA = "hibernate.default_schema";
```

通过上面的分析，说明想要使用hibernate在不同的schema中生成相同的表，只要设置合适的schema就可以了，具体的配置就是：

```yaml
spring:
  jpa:
    properties:
      hibernate:
        default_schema: working_data
        dialect: org.hibernate.dialect.PostgreSQL82Dialect
        temp:
          use_jdbc_metadata_defaults: false
```

