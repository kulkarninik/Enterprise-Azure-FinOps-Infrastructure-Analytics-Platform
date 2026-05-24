# generate_enterprise_infra_data.py

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import json

fake = Faker()
Faker.seed(2024)
np.random.seed(2024)

# ============================================
# 1. AZURE RESOURCE INVENTORY
# ============================================

def generate_resource_inventory(n_resources=500):
    """Generate Azure resource inventory"""
    
    resource_types = {
        'VirtualMachine': 200,
        'StorageAccount': 100,
        'SQLDatabase': 50,
        'AppServicePlan': 30,
        'LoadBalancer': 20,
        'NetworkInterface': 200,
        'PublicIPAddress': 50,
        'CosmosDB': 10,
        'KeyVault': 15,
        'DataFactory': 10,
        'ContainerInstance': 15
    }
    
    regions = ['East US', 'West US', 'West Europe', 'Southeast Asia', 'UK South']
    environments = ['Production', 'Development', 'Testing', 'Staging']
    departments = ['Engineering', 'Sales', 'Finance', 'Marketing', 'HR', 'Operations']
    subscriptions = ['Prod-Subscription', 'Dev-Subscription', 'Test-Subscription']
    
    resources = []
    resource_id_counter = 1000
    
    for res_type, count in resource_types.items():
        for i in range(count):
            env = random.choice(environments)
            dept = random.choice(departments)
            region = random.choice(regions)
            subscription = random.choice(subscriptions)
            
            # Naming convention based on type
            if res_type == 'VirtualMachine':
                name = f"vm-{env.lower()[:4]}-{dept.lower()[:3]}-{i+1:03d}"
            elif res_type == 'StorageAccount':
                name = f"st{dept.lower()[:3]}{env.lower()[:4]}{i+1:03d}"
            elif res_type == 'SQLDatabase':
                name = f"sqldb-{env.lower()[:4]}-{dept.lower()[:3]}-{i+1:02d}"
            else:
                name = f"{res_type.lower()}-{i+1:03d}"
            
            # Resource group naming
            rg_name = f"rg-{dept.lower()}-{env.lower()}-{region.lower().replace(' ', '')}"
            
            # Created date (last 2 years)
            created_date = fake.date_between(start_date='-730d', end_date='-30d')
            
            # Status logic
            if env == 'Production':
                status = random.choices(['Running', 'Stopped'], weights=[95, 5])[0]
            else:
                status = random.choices(['Running', 'Stopped', 'Deallocated'], weights=[60, 20, 20])[0]
            
            # Tags
            tags = {
                'Environment': env,
                'Department': dept,
                'Owner': fake.email(),
                'CostCenter': f'CC-{random.randint(1000, 9999)}',
                'Project': fake.catch_phrase().replace(' ', '-')
            }
            
            resources.append({
                'resource_id': f'/subscriptions/sub-{random.randint(1000,9999)}/resourceGroups/{rg_name}/providers/Microsoft.Compute/{res_type}/{name}',
                'resource_name': name,
                'resource_type': res_type,
                'region': region,
                'subscription_name': subscription,
                'resource_group': rg_name,
                'environment': env,
                'department': dept,
                'created_date': created_date,
                'tags': json.dumps(tags),
                'status': status,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            resource_id_counter += 1
    
    return pd.DataFrame(resources)

# ============================================
# 2. COST & BILLING DATA
# ============================================

def generate_cost_billing_data(resources_df, days=90):
    """Generate daily cost data for each resource"""
    
    # Cost per resource type per day (baseline)
    cost_baseline = {
        'VirtualMachine': (50, 500),  # min, max USD per day
        'StorageAccount': (5, 100),
        'SQLDatabase': (100, 800),
        'AppServicePlan': (30, 300),
        'LoadBalancer': (20, 100),
        'NetworkInterface': (1, 5),
        'PublicIPAddress': (3, 10),
        'CosmosDB': (200, 1500),
        'KeyVault': (0.5, 5),
        'DataFactory': (10, 200),
        'ContainerInstance': (20, 150)
    }
    
    service_categories = {
        'VirtualMachine': 'Compute',
        'StorageAccount': 'Storage',
        'SQLDatabase': 'Database',
        'AppServicePlan': 'Compute',
        'LoadBalancer': 'Networking',
        'NetworkInterface': 'Networking',
        'PublicIPAddress': 'Networking',
        'CosmosDB': 'Database',
        'KeyVault': 'Security',
        'DataFactory': 'Analytics',
        'ContainerInstance': 'Compute'
    }
    
    pricing_models = ['PayAsYouGo', 'Reserved', 'Spot']
    
    cost_records = []
    
    for _, resource in resources_df.iterrows():
        res_type = resource['resource_type']
        min_cost, max_cost = cost_baseline.get(res_type, (1, 10))
        
        # Base cost for this resource
        base_cost = random.uniform(min_cost, max_cost)
        
        # Environment multiplier
        env_multiplier = {
            'Production': 1.0,
            'Staging': 0.6,
            'Development': 0.3,
            'Testing': 0.2
        }.get(resource['environment'], 0.5)
        
        # Generate daily costs for last N days
        for day_offset in range(days):
            cost_date = datetime.now().date() - timedelta(days=day_offset)
            
            # Status-based cost
            if resource['status'] == 'Running':
                daily_cost = base_cost * env_multiplier
            elif resource['status'] == 'Stopped':
                daily_cost = base_cost * 0.3  # Storage costs remain
            else:  # Deallocated
                daily_cost = base_cost * 0.1
            
            # Add random variation (+/- 15%)
            daily_cost = daily_cost * random.uniform(0.85, 1.15)
            
            # Pricing model affects cost
            pricing = random.choices(pricing_models, weights=[70, 20, 10])[0]
            if pricing == 'Reserved':
                daily_cost *= 0.6  # 40% savings
            elif pricing == 'Spot':
                daily_cost *= 0.3  # 70% savings but for Dev/Test only
            
            # Quantity (usage hours, GB, etc.)
            quantity = random.uniform(1, 24) if res_type == 'VirtualMachine' else random.uniform(10, 1000)
            
            cost_records.append({
                'date': cost_date,
                'resource_id': resource['resource_id'],
                'resource_name': resource['resource_name'],
                'resource_type': res_type,
                'service_category': service_categories.get(res_type, 'Other'),
                'meter_name': f"{res_type} - Hours" if res_type in ['VirtualMachine'] else f"{res_type} - GB",
                'cost_usd': round(daily_cost, 2),
                'quantity': round(quantity, 2),
                'subscription_name': resource['subscription_name'],
                'department': resource['department'],
                'region': resource['region'],
                'pricing_model': pricing,
                'environment': resource['environment']
            })
    
    return pd.DataFrame(cost_records)

# ============================================
# 3. VM PERFORMANCE METRICS
# ============================================

def generate_vm_performance_metrics(resources_df, hours=168):  # 1 week
    """Generate VM performance metrics (5-min intervals)"""
    
    vms = resources_df[resources_df['resource_type'] == 'VirtualMachine'].copy()
    
    vm_sizes = ['Standard_B2s', 'Standard_D4s_v3', 'Standard_E8s_v4', 'Standard_F16s_v2']
    
    metrics = []
    
    for _, vm in vms.iterrows():
        vm_size = random.choice(vm_sizes)
        
        # Performance characteristics by environment
        if vm['environment'] == 'Production':
            cpu_baseline = random.uniform(40, 70)
            memory_baseline = random.uniform(50, 75)
        else:
            cpu_baseline = random.uniform(10, 40)
            memory_baseline = random.uniform(20, 50)
        
        # Generate metrics every 5 minutes for the last week
        intervals = hours * 12  # 5-min intervals
        
        for i in range(intervals):
            timestamp = datetime.now() - timedelta(minutes=5 * i)
            
            # Simulate daily patterns (higher usage during business hours)
            hour = timestamp.hour
            if 9 <= hour <= 17:  # Business hours
                time_multiplier = 1.3
            else:
                time_multiplier = 0.7
            
            # Add random spikes (5% chance)
            spike = random.random() < 0.05
            
            if vm['status'] == 'Running':
                cpu = cpu_baseline * time_multiplier + random.uniform(-10, 10)
                if spike:
                    cpu = min(98, cpu + random.uniform(20, 40))
                cpu = max(0, min(100, cpu))
                
                memory = memory_baseline * time_multiplier + random.uniform(-5, 5)
                memory = max(0, min(100, memory))
                
                disk_read = random.randint(50, 500)
                disk_write = random.randint(50, 400)
                network_in = random.uniform(10, 500)
                network_out = random.uniform(10, 400)
            else:
                cpu = 0
                memory = 0
                disk_read = 0
                disk_write = 0
                network_in = 0
                network_out = 0
            
            metrics.append({
                'timestamp': timestamp,
                'vm_name': vm['resource_name'],
                'resource_id': vm['resource_id'],
                'cpu_percent': round(cpu, 2),
                'memory_percent': round(memory, 2),
                'disk_read_iops': disk_read,
                'disk_write_iops': disk_write,
                'network_in_mbps': round(network_in, 2),
                'network_out_mbps': round(network_out, 2),
                'vm_size': vm_size,
                'region': vm['region'],
                'environment': vm['environment'],
                'status': vm['status']
            })
    
    return pd.DataFrame(metrics)

# ============================================
# 4. STORAGE METRICS
# ============================================

def generate_storage_metrics(resources_df, days=30):
    """Generate storage account metrics"""
    
    storage_accounts = resources_df[resources_df['resource_type'] == 'StorageAccount'].copy()
    
    tiers = ['Hot', 'Cool', 'Archive']
    
    metrics = []
    
    for _, storage in storage_accounts.iterrows():
        tier = random.choice(tiers)
        base_capacity = random.uniform(100, 10000)  # GB
        
        for day in range(days):
            metric_date = datetime.now() - timedelta(days=day)
            
            # Storage grows over time
            capacity = base_capacity + (day * random.uniform(1, 50))
            blob_capacity = capacity * random.uniform(0.6, 0.9)
            
            # Transactions vary by tier
            if tier == 'Hot':
                transactions = random.randint(10000, 500000)
                cost_per_gb = 0.0184
            elif tier == 'Cool':
                transactions = random.randint(1000, 50000)
                cost_per_gb = 0.01
            else:  # Archive
                transactions = random.randint(100, 5000)
                cost_per_gb = 0.002
            
            egress = random.uniform(10, 500)
            
            daily_cost = (capacity * cost_per_gb / 30) + (transactions * 0.000004) + (egress * 0.087 / 1000)
            
            metrics.append({
                'timestamp': metric_date,
                'storage_account_name': storage['resource_name'],
                'resource_id': storage['resource_id'],
                'total_capacity_gb': round(capacity, 2),
                'blob_capacity_gb': round(blob_capacity, 2),
                'transaction_count': transactions,
                'egress_gb': round(egress, 2),
                'tier': tier,
                'cost_usd': round(daily_cost, 2),
                'department': storage['department'],
                'environment': storage['environment']
            })
    
    return pd.DataFrame(metrics)

# ============================================
# 5. DATABASE PERFORMANCE METRICS
# ============================================

def generate_database_metrics(resources_df, days=7):
    """Generate database performance metrics"""
    
    databases = resources_df[resources_df['resource_type'].isin(['SQLDatabase', 'CosmosDB'])].copy()
    
    metrics = []
    
    for _, db in databases.iterrows():
        db_type = 'SQL' if db['resource_type'] == 'SQLDatabase' else 'CosmosDB'
        
        # Hourly metrics for last 7 days
        for hour in range(days * 24):
            timestamp = datetime.now() - timedelta(hours=hour)
            
            if db['environment'] == 'Production':
                dtu_percent = random.uniform(50, 85)
                connections = random.randint(50, 500)
            else:
                dtu_percent = random.uniform(10, 50)
                connections = random.randint(5, 100)
            
            storage_percent = random.uniform(30, 80)
            deadlocks = random.choices([0, 1, 2, 3], weights=[85, 10, 4, 1])[0]
            query_duration = random.uniform(50, 500)
            
            # Cost based on DTU utilization
            base_cost = 10 if db_type == 'SQL' else 30
            daily_cost = base_cost * (dtu_percent / 100) * random.uniform(0.9, 1.1)
            
            metrics.append({
                'timestamp': timestamp,
                'database_name': db['resource_name'],
                'database_type': db_type,
                'resource_id': db['resource_id'],
                'dtu_percent': round(dtu_percent, 2),
                'storage_percent': round(storage_percent, 2),
                'connection_count': connections,
                'deadlocks': deadlocks,
                'query_duration_avg_ms': round(query_duration, 2),
                'cost_usd': round(daily_cost, 2),
                'environment': db['environment'],
                'region': db['region']
            })
    
    return pd.DataFrame(metrics)

# ============================================
# 6. OPTIMIZATION RECOMMENDATIONS
# ============================================

def generate_optimization_recommendations(resources_df, vm_metrics_df):
    """Generate cost optimization recommendations"""
    
    recommendations = []
    rec_id = 1
    
    # Analyze VMs for right-sizing opportunities
    vms = resources_df[resources_df['resource_type'] == 'VirtualMachine'].copy()
    
    for _, vm in vms.iterrows():
        # Get average CPU/Memory for this VM
        vm_perf = vm_metrics_df[vm_metrics_df['vm_name'] == vm['resource_name']]
        
        if len(vm_perf) > 0:
            avg_cpu = vm_perf['cpu_percent'].mean()
            avg_memory = vm_perf['memory_percent'].mean()
            
            current_sku = random.choice(['Standard_D4s_v3', 'Standard_E8s_v4', 'Standard_F16s_v2'])
            current_cost = random.uniform(100, 500)
            
            # Underutilized VM (< 30% CPU)
            if avg_cpu < 30 and vm['status'] == 'Running':
                recommendations.append({
                    'recommendation_id': f'REC-{rec_id:05d}',
                    'date_generated': datetime.now().date(),
                    'resource_name': vm['resource_name'],
                    'resource_type': vm['resource_type'],
                    'recommendation_type': 'RightSize',
                    'current_sku': current_sku,
                    'recommended_sku': 'Standard_B2s',
                    'current_monthly_cost_usd': round(current_cost * 30, 2),
                    'estimated_monthly_cost_usd': round(current_cost * 30 * 0.4, 2),
                    'estimated_savings_usd': round(current_cost * 30 * 0.6, 2),
                    'savings_percentage': 60,
                    'impact': 'Medium',
                    'confidence': 'High',
                    'reason': f'VM averaging {avg_cpu:.1f}% CPU utilization over 7 days',
                    'department': vm['department'],
                    'environment': vm['environment']
                })
                rec_id += 1
            
            # Stopped VM costing money
            elif vm['status'] == 'Stopped':
                recommendations.append({
                    'recommendation_id': f'REC-{rec_id:05d}',
                    'date_generated': datetime.now().date(),
                    'resource_name': vm['resource_name'],
                    'resource_type': vm['resource_type'],
                    'recommendation_type': 'Shutdown',
                    'current_sku': current_sku,
                    'recommended_sku': 'Deallocate',
                    'current_monthly_cost_usd': round(current_cost * 30 * 0.3, 2),
                    'estimated_monthly_cost_usd': 0,
                    'estimated_savings_usd': round(current_cost * 30 * 0.3, 2),
                    'savings_percentage': 100,
                    'impact': 'High',
                    'confidence': 'High',
                    'reason': 'VM stopped but not deallocated - still incurring storage costs',
                    'department': vm['department'],
                    'environment': vm['environment']
                })
                rec_id += 1
            
            # Reserved Instance recommendation for Production VMs
            elif vm['environment'] == 'Production' and avg_cpu > 50:
                recommendations.append({
                    'recommendation_id': f'REC-{rec_id:05d}',
                    'date_generated': datetime.now().date(),
                    'resource_name': vm['resource_name'],
                    'resource_type': vm['resource_type'],
                    'recommendation_type': 'Reserved Instance',
                    'current_sku': current_sku,
                    'recommended_sku': f'{current_sku} (1-Year Reserved)',
                    'current_monthly_cost_usd': round(current_cost * 30, 2),
                    'estimated_monthly_cost_usd': round(current_cost * 30 * 0.65, 2),
                    'estimated_savings_usd': round(current_cost * 30 * 0.35, 2),
                    'savings_percentage': 35,
                    'impact': 'High',
                    'confidence': 'High',
                    'reason': 'Production VM with consistent usage - eligible for Reserved Instance pricing',
                    'department': vm['department'],
                    'environment': vm['environment']
                })
                rec_id += 1
    
    return pd.DataFrame(recommendations)

# ============================================
# 7. BUDGET ALERTS
# ============================================

def generate_budget_alerts(cost_df):
    """Generate budget alert events"""
    
    # Group costs by department and month
    cost_df['month'] = pd.to_datetime(cost_df['date']).dt.to_period('M')
    monthly_dept_costs = cost_df.groupby(['month', 'department'])['cost_usd'].sum().reset_index()
    
    alerts = []
    alert_id = 1
    
    for _, row in monthly_dept_costs.iterrows():
        dept = row['department']
        actual_spend = row['cost_usd']
        
        # Set budget (random for demo)
        budget = random.uniform(50000, 200000)
        threshold_80 = budget * 0.8
        threshold_100 = budget
        
        alert_level = None
        if actual_spend >= threshold_100:
            alert_level = 'Critical'
            message = f'{dept} exceeded monthly budget'
        elif actual_spend >= threshold_80:
            alert_level = 'Warning'
            message = f'{dept} at 80% of monthly budget'
        
        if alert_level:
            alerts.append({
                'alert_id': f'ALERT-{alert_id:05d}',
                'alert_date': datetime.now().date(),
                'department': dept,
                'month': str(row['month']),
                'budget_usd': round(budget, 2),
                'actual_spend_usd': round(actual_spend, 2),
                'variance_usd': round(actual_spend - budget, 2),
                'variance_percentage': round((actual_spend - budget) / budget * 100, 2),
                'alert_level': alert_level,
                'threshold_breached': '100%' if actual_spend >= threshold_100 else '80%',
                'message': message,
                'action_required': 'Yes' if alert_level == 'Critical' else 'Monitor'
            })
            alert_id += 1
    
    return pd.DataFrame(alerts) if alerts else pd.DataFrame()

# ============================================
# MAIN EXECUTION
# ============================================

print("="*60)
print("🚀 Generating Enterprise Infrastructure Cost Data")
print("="*60)

# 1. Generate resource inventory
print("\n📦 Step 1/7: Generating Azure Resource Inventory...")
resources_df = generate_resource_inventory(n_resources=500)
print(f"   ✅ Generated {len(resources_df)} resources")

# 2. Generate cost data
print("\n💰 Step 2/7: Generating Cost & Billing Data (90 days)...")
cost_df = generate_cost_billing_data(resources_df, days=90)
print(f"   ✅ Generated {len(cost_df)} cost records")

# 3. Generate VM performance metrics
print("\n📊 Step 3/7: Generating VM Performance Metrics (7 days, 5-min intervals)...")
vm_metrics_df = generate_vm_performance_metrics(resources_df, hours=168)
print(f"   ✅ Generated {len(vm_metrics_df)} VM metric records")

# 4. Generate storage metrics
print("\n💾 Step 4/7: Generating Storage Metrics (30 days)...")
storage_metrics_df = generate_storage_metrics(resources_df, days=30)
print(f"   ✅ Generated {len(storage_metrics_df)} storage metric records")

# 5. Generate database metrics
print("\n🗄️  Step 5/7: Generating Database Performance Metrics (7 days)...")
db_metrics_df = generate_database_metrics(resources_df, days=7)
print(f"   ✅ Generated {len(db_metrics_df)} database metric records")

# 6. Generate optimization recommendations
print("\n💡 Step 6/7: Generating Cost Optimization Recommendations...")
recommendations_df = generate_optimization_recommendations(resources_df, vm_metrics_df)
print(f"   ✅ Generated {len(recommendations_df)} recommendations")

# 7. Generate budget alerts
print("\n🚨 Step 7/7: Generating Budget Alerts...")
alerts_df = generate_budget_alerts(cost_df)
print(f"   ✅ Generated {len(alerts_df)} budget alerts")

# ============================================
# SAVE TO CSV
# ============================================

print("\n💾 Saving datasets to CSV files...")

datasets = {
    'azure_resource_inventory.csv': resources_df,
    'cost_billing_data.csv': cost_df,
    'vm_performance_metrics.csv': vm_metrics_df,
    'storage_metrics.csv': storage_metrics_df,
    'database_metrics.csv': db_metrics_df,
    'optimization_recommendations.csv': recommendations_df,
    'budget_alerts.csv': alerts_df
}

for filename, df in datasets.items():
    df.to_csv(filename, index=False)
    print(f"   ✅ {filename} ({len(df)} records)")

# ============================================
# SUMMARY STATISTICS
# ============================================

print("\n" + "="*60)
print("📈 DATA SUMMARY")
print("="*60)

total_cost = cost_df['cost_usd'].sum()
total_savings = recommendations_df['estimated_savings_usd'].sum() if len(recommendations_df) > 0 else 0

print(f"""
📊 Resource Inventory:      {len(resources_df):,} resources
💰 Total Cost (90 days):    ${total_cost:,.2f}
💡 Optimization Opportunities: {len(recommendations_df)}
💵 Potential Savings/Month: ${total_savings:,.2f}
🚨 Budget Alerts:           {len(alerts_df)}

📁 Files Generated:
   • azure_resource_inventory.csv
   • cost_billing_data.csv
   • vm_performance_metrics.csv
   • storage_metrics.csv
   • database_metrics.csv
   • optimization_recommendations.csv
   • budget_alerts.csv
""")

print("="*60)
print("✅ Data generation complete!")
print("="*60)