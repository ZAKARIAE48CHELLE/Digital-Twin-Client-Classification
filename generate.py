# ============================================================
# Generate augmented CLV transaction dataset from OSMOS Digital Twin data
# ============================================================

import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta

# ============================================================
# 1. Configuration
# ============================================================

INPUT_FILE = Path("osmos_digital_twin_data.xlsx")
OUTPUT_FILE = "osmos_augmented_clv_training_dataset.xlsx"

DIGITAL_TWIN_SHEET = "Digital_Twins"

AUGMENTATION_FACTOR = 100
RANDOM_SEED = 42

OBS_START = pd.Timestamp("2025-01-01")
OBS_END = pd.Timestamp("2025-06-30")

FUTURE_START = pd.Timestamp("2025-07-01")
FUTURE_END = pd.Timestamp("2025-12-31")

BASE_PROFIT_MARGIN = 0.25

rng = np.random.default_rng(RANDOM_SEED)

# ============================================================
# 2. Load Digital Twin data
# ============================================================

df = pd.read_excel(INPUT_FILE, sheet_name=DIGITAL_TWIN_SHEET)

df["entity_type"] = df["entity_type"].astype(str)

clients_df = df[
    (df["entity_type"].str.lower() == "client") &
    (pd.to_numeric(df["purchases_90d"], errors="coerce").fillna(0) > 0) &
    (pd.to_numeric(df["total_spent_90d_mad"], errors="coerce").fillna(0) > 0)
].copy()

print("Original rows:", len(df))
print("Valid client rows used as base:", len(clients_df))

if len(clients_df) == 0:
    raise ValueError("No valid clients with purchase history found.")

# ============================================================
# 3. Helper functions
# ============================================================

def safe_float(row, col, default=0.0):
    val = row.get(col, default)
    try:
        if pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default


def safe_str(row, col, default="Unknown"):
    val = row.get(col, default)
    if pd.isna(val):
        return default
    return str(val)


def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def perturb_positive(value, noise=0.25, min_value=0.0):
    value = max(float(value), min_value)
    factor = rng.lognormal(mean=0.0, sigma=noise)
    return max(value * factor, min_value)


def perturb_score(value, noise=0.06):
    return clip01(float(value) + rng.normal(0, noise))


def class_future_multiplier(dynamic_class):
    dynamic_class = str(dynamic_class)

    if dynamic_class == "VIP Client":
        return 1.35
    elif dynamic_class == "Loyal Client":
        return 1.20
    elif dynamic_class == "Active Client":
        return 1.00
    elif dynamic_class == "New Client":
        return 0.85
    elif dynamic_class == "Dormant Client":
        return 0.40
    elif dynamic_class == "Churn Risk Client":
        return 0.25
    else:
        return 0.80


def random_dates(start, end, n):
    if n <= 0:
        return []

    total_days = (end - start).days
    days = rng.integers(0, total_days + 1, size=n)

    dates = [
        start + pd.Timedelta(days=int(d))
        for d in days
    ]

    return sorted(dates)


def random_observation_dates(start, end, n, recency_days):
    if n <= 0:
        return []

    total_days = (end - start).days
    recency_days = int(np.clip(recency_days, 0, total_days))

    last_date = end - pd.Timedelta(days=recency_days)

    if n == 1:
        return [last_date]

    earlier_dates = random_dates(start, last_date, n - 1)
    dates = earlier_dates + [last_date]

    return sorted(dates)


def choose_category(preferred_category):
    categories = ["Electronics", "Fashion", "Home", "Beauty", "Sports"]

    preferred_category = str(preferred_category)
    if preferred_category not in categories:
        preferred_category = rng.choice(categories)

    if rng.random() < 0.70:
        return preferred_category
    else:
        return rng.choice(categories)


def generate_transaction(
    customer_id,
    order_id,
    order_date,
    preferred_category,
    avg_order_value,
    churn_risk,
    price_sensitivity,
    region,
    source_channel
):
    category = choose_category(preferred_category)

    amount = rng.lognormal(
        mean=np.log(max(avg_order_value, 50)),
        sigma=0.35
    )

    amount = float(np.clip(amount, 20, max(avg_order_value * 4, 200)))

    discount_rate = np.clip(
        rng.normal(loc=0.05 + 0.10 * price_sensitivity, scale=0.04),
        0.0,
        0.40
    )

    discount_amount = amount * discount_rate

    return_probability = np.clip(
        0.02 + 0.08 * churn_risk + rng.normal(0, 0.02),
        0.0,
        0.30
    )

    returned = rng.random() < return_probability

    net_amount = -amount if returned else amount

    margin_rate = np.clip(
        rng.normal(BASE_PROFIT_MARGIN, 0.04),
        0.08,
        0.45
    )

    profit_mad = net_amount * margin_rate

    return {
        "customer_id": customer_id,
        "order_id": order_id,
        "order_date": order_date,
        "order_amount_mad": round(amount, 2),
        "discount_amount_mad": round(discount_amount, 2),
        "net_amount_mad": round(net_amount, 2),
        "profit_margin_rate": round(margin_rate, 4),
        "profit_mad": round(profit_mad, 2),
        "product_category": category,
        "quantity": int(rng.integers(1, 5)),
        "returned": bool(returned),
        "region": region,
        "source_channel": source_channel
    }


# ============================================================
# 4. Generate synthetic customers and transactions
# ============================================================

customers = []
transactions = []

order_counter = 1

for _, base_row in clients_df.iterrows():

    base_entity_id = safe_str(base_row, "entity_id")

    base_purchases_90d = safe_float(base_row, "purchases_90d", 1)
    base_total_spent = safe_float(base_row, "total_spent_90d_mad", 100)
    base_aov = safe_float(base_row, "avg_order_value_mad", 0)

    if base_aov <= 0 and base_purchases_90d > 0:
        base_aov = base_total_spent / base_purchases_90d

    base_aov = max(base_aov, 50)

    for aug_idx in range(AUGMENTATION_FACTOR):

        customer_id = f"{base_entity_id}_AUG{aug_idx + 1:03d}"

        dynamic_class = safe_str(base_row, "dynamic_class", "Active Client")

        rfm_score = perturb_score(safe_float(base_row, "rfm_score", 0.5), noise=0.05)
        churn_risk = perturb_score(safe_float(base_row, "churn_risk_score", 0.2), noise=0.08)

        recency_days = max(
            0,
            int(round(perturb_positive(safe_float(base_row, "recency_days", 30), noise=0.35)))
        )

        visits_30d = max(
            0,
            int(round(perturb_positive(safe_float(base_row, "visits_30d", 1), noise=0.45)))
        )

        product_views_30d = max(
            0,
            int(round(perturb_positive(safe_float(base_row, "product_views_30d", 1), noise=0.45)))
        )

        cart_additions_30d = max(
            0,
            int(round(perturb_positive(safe_float(base_row, "cart_additions_30d", 0), noise=0.50)))
        )

        email_open_rate = perturb_score(safe_float(base_row, "email_open_rate", 0.0), noise=0.04)
        email_click_rate = perturb_score(safe_float(base_row, "email_click_rate", 0.0), noise=0.03)
        social_sentiment_avg = perturb_score(safe_float(base_row, "social_sentiment_avg", 0.5), noise=0.08)

        price_sensitivity = perturb_score(safe_float(base_row, "price_sensitivity", 0.5), noise=0.07)
        income_power_score = perturb_score(safe_float(base_row, "income_power_score", 0.5), noise=0.07)

        avg_order_value = perturb_positive(base_aov, noise=0.30, min_value=50)

        # Convert 90-day purchase behavior to 6-month observation window
        expected_obs_tx = max(1.0, base_purchases_90d * 2)

        obs_tx_count = max(
            1,
            int(rng.poisson(expected_obs_tx * rng.lognormal(0, 0.25)))
        )

        retention_probability = np.clip(1.0 - churn_risk, 0.05, 1.0)

        future_multiplier = class_future_multiplier(dynamic_class)

        future_lambda = (
            obs_tx_count
            * retention_probability
            * future_multiplier
            * (0.60 + 0.80 * rfm_score)
        )

        future_tx_count = int(rng.poisson(max(future_lambda, 0.1)))

        preferred_category = safe_str(base_row, "preferred_category", "Unknown")
        region = safe_str(base_row, "region", "Unknown")
        source_channel = safe_str(base_row, "source_channel", "Unknown")

        customer_record = base_row.to_dict()
        customer_record.update({
            "customer_id": customer_id,
            "base_entity_id": base_entity_id,
            "entity_id": customer_id,
            "entity_type": "Client",
            "dynamic_class": dynamic_class,
            "recency_days": recency_days,
            "visits_30d": visits_30d,
            "product_views_30d": product_views_30d,
            "cart_additions_30d": cart_additions_30d,
            "email_open_rate": email_open_rate,
            "email_click_rate": email_click_rate,
            "social_sentiment_avg": social_sentiment_avg,
            "price_sensitivity": price_sensitivity,
            "income_power_score": income_power_score,
            "rfm_score": rfm_score,
            "churn_risk_score": churn_risk,
            "avg_order_value_mad": avg_order_value,
            "synthetic_customer": True
        })

        customers.append(customer_record)

        obs_dates = random_observation_dates(
            OBS_START,
            OBS_END,
            obs_tx_count,
            recency_days
        )

        future_dates = random_dates(
            FUTURE_START,
            FUTURE_END,
            future_tx_count
        )

        for order_date in obs_dates:
            tx = generate_transaction(
                customer_id=customer_id,
                order_id=f"O{order_counter:09d}",
                order_date=order_date,
                preferred_category=preferred_category,
                avg_order_value=avg_order_value,
                churn_risk=churn_risk,
                price_sensitivity=price_sensitivity,
                region=region,
                source_channel=source_channel
            )
            tx["period"] = "observation"
            transactions.append(tx)
            order_counter += 1

        for order_date in future_dates:
            tx = generate_transaction(
                customer_id=customer_id,
                order_id=f"O{order_counter:09d}",
                order_date=order_date,
                preferred_category=preferred_category,
                avg_order_value=avg_order_value,
                churn_risk=churn_risk,
                price_sensitivity=price_sensitivity,
                region=region,
                source_channel=source_channel
            )
            tx["period"] = "future"
            transactions.append(tx)
            order_counter += 1


customers_aug = pd.DataFrame(customers)
transactions_aug = pd.DataFrame(transactions)

transactions_aug["order_date"] = pd.to_datetime(transactions_aug["order_date"])

print("Generated customers:", len(customers_aug))
print("Generated transactions:", len(transactions_aug))
print(transactions_aug["period"].value_counts())

# ============================================================
# 5. Build CLV training table
# ============================================================

training_rows = []

# Convert to dict for fast O(1) lookups in loop
customers_dict = customers_aug.set_index("customer_id").to_dict(orient="index")

for customer_id, cust_tx in transactions_aug.groupby("customer_id"):

    obs_tx = cust_tx[cust_tx["period"] == "observation"].copy()
    future_tx = cust_tx[cust_tx["period"] == "future"].copy()

    customer_row = customers_dict.get(customer_id, {})

    obs_tx = obs_tx.sort_values("order_date")

    transaction_count_obs = len(obs_tx)

    if transaction_count_obs > 0:
        first_purchase_date = obs_tx["order_date"].min()
        last_purchase_date = obs_tx["order_date"].max()

        customer_age_days = max(
            1,
            (OBS_END - first_purchase_date).days
        )

        recency_obs_days = max(
            0,
            (OBS_END - last_purchase_date).days
        )

        purchase_dates = obs_tx["order_date"].sort_values().values

        if len(purchase_dates) >= 2:
            intervals = np.diff(purchase_dates).astype("timedelta64[D]").astype(int)
            purchase_interval_mean_days = float(np.mean(intervals))
            purchase_interval_std_days = float(np.std(intervals))
        else:
            purchase_interval_mean_days = customer_age_days
            purchase_interval_std_days = 0.0

        total_spent_obs = obs_tx["net_amount_mad"].sum()
        total_profit_obs = obs_tx["profit_mad"].sum()

        avg_order_value_obs = obs_tx["order_amount_mad"].mean()

        return_rate_obs = obs_tx["returned"].mean()
        discount_rate_obs = (
            obs_tx["discount_amount_mad"].sum() /
            max(obs_tx["order_amount_mad"].sum(), 1)
        )

        category_diversity_obs = obs_tx["product_category"].nunique()

    else:
        first_purchase_date = pd.NaT
        last_purchase_date = pd.NaT
        customer_age_days = 0
        recency_obs_days = 999
        purchase_interval_mean_days = 999
        purchase_interval_std_days = 0
        total_spent_obs = 0
        total_profit_obs = 0
        avg_order_value_obs = 0
        return_rate_obs = 0
        discount_rate_obs = 0
        category_diversity_obs = 0

    clv_amount_mad = max(0.0, future_tx["profit_mad"].sum())

    row = {
        "customer_id": customer_id,
        "base_entity_id": customer_row.get("base_entity_id"),
        "dynamic_class": customer_row.get("dynamic_class"),
        "region": customer_row.get("region"),
        "source_channel": customer_row.get("source_channel"),
        "segment": customer_row.get("segment"),
        "persona": customer_row.get("persona"),
        "age_group": customer_row.get("age_group"),
        "preferred_device": customer_row.get("preferred_device"),
        "preferred_category": customer_row.get("preferred_category"),
        "marketing_consent": customer_row.get("marketing_consent"),
        "price_sensitivity": customer_row.get("price_sensitivity"),
        "income_power_score": customer_row.get("income_power_score"),
        "initial_interest_score": customer_row.get("initial_interest_score"),

        # Observation-window CLV features
        "frequency_obs": transaction_count_obs,
        "recency_obs_days": recency_obs_days,
        "customer_age_days": customer_age_days,
        "purchase_interval_mean_days": purchase_interval_mean_days,
        "purchase_interval_std_days": purchase_interval_std_days,
        "total_spent_obs_mad": total_spent_obs,
        "avg_order_value_obs_mad": avg_order_value_obs,
        "total_profit_obs_mad": total_profit_obs,
        "return_rate_obs": return_rate_obs,
        "discount_rate_obs": discount_rate_obs,
        "category_diversity_obs": category_diversity_obs,
        "transaction_count_obs": transaction_count_obs,

        # Digital Twin features
        "recency_days": customer_row.get("recency_days"),
        "visits_30d": customer_row.get("visits_30d"),
        "product_views_30d": customer_row.get("product_views_30d"),
        "cart_additions_30d": customer_row.get("cart_additions_30d"),
        "purchases_90d": customer_row.get("purchases_90d"),
        "total_spent_90d_mad": customer_row.get("total_spent_90d_mad"),
        "avg_order_value_mad": customer_row.get("avg_order_value_mad"),
        "email_open_rate": customer_row.get("email_open_rate"),
        "email_click_rate": customer_row.get("email_click_rate"),
        "complaint_count_90d": customer_row.get("complaint_count_90d"),
        "review_score_avg": customer_row.get("review_score_avg"),
        "social_mentions_30d": customer_row.get("social_mentions_30d"),
        "social_sentiment_avg": customer_row.get("social_sentiment_avg"),
        "rfm_score": customer_row.get("rfm_score"),
        "conversion_probability": customer_row.get("conversion_probability"),
        "churn_risk_score": customer_row.get("churn_risk_score"),
        "behavioral_engagement_score": customer_row.get("behavioral_engagement_score"),
        "predictive_value_score": customer_row.get("predictive_value_score"),
        "decision_priority_score": customer_row.get("decision_priority_score"),

        # Target
        "clv_amount_mad": clv_amount_mad,

        # Useful but should NOT be used as input features
        "transaction_count_future": len(future_tx)
    }

    training_rows.append(row)

clv_training = pd.DataFrame(training_rows)

# Remove invalid rows
clv_training = clv_training[
    clv_training["frequency_obs"] > 0
].copy()

# ============================================================
# 6. Create CLV score and segment from target
# ============================================================

clv_training["clv_score"] = (
    clv_training["clv_amount_mad"]
    .rank(pct=True)
    * 100
)

def score_to_segment(score):
    if score <= 25:
        return "Low Future Value"
    elif score <= 50:
        return "Medium Future Value"
    elif score <= 75:
        return "High Future Value"
    else:
        return "Very High Future Value"

clv_training["clv_segment"] = clv_training["clv_score"].apply(score_to_segment)

# ============================================================
# 7. Summary sheet
# ============================================================

summary = pd.DataFrame({
    "metric": [
        "original_rows",
        "valid_base_clients",
        "augmentation_factor",
        "generated_customers",
        "generated_transactions",
        "observation_transactions",
        "future_transactions",
        "training_rows",
        "mean_clv_amount_mad",
        "median_clv_amount_mad",
        "max_clv_amount_mad"
    ],
    "value": [
        len(df),
        len(clients_df),
        AUGMENTATION_FACTOR,
        len(customers_aug),
        len(transactions_aug),
        len(transactions_aug[transactions_aug["period"] == "observation"]),
        len(transactions_aug[transactions_aug["period"] == "future"]),
        len(clv_training),
        round(clv_training["clv_amount_mad"].mean(), 2),
        round(clv_training["clv_amount_mad"].median(), 2),
        round(clv_training["clv_amount_mad"].max(), 2)
    ]
})

print("\nCLV training table shape:", clv_training.shape)
print("\nCLV target statistics:")
print(clv_training["clv_amount_mad"].describe())

print("\nCLV segment distribution:")
print(clv_training["clv_segment"].value_counts())

# ============================================================
# 8. Save Excel output
# ============================================================

# Cap transactions to fit Excel's maximum row limit (1,048,576)
excel_txn_cap = 1048500
if len(transactions_aug) > excel_txn_cap:
    print(f"\nWARNING: Transactions count ({len(transactions_aug):,}) exceeds Excel sheet limit (1,048,576).")
    print(f"Capping Excel sheet 'Transactions' to the first {excel_txn_cap:,} rows to prevent file corruption/crashes.")
    transactions_excel = transactions_aug.head(excel_txn_cap)
    
    # Save the full transactions to CSV for safety/completeness
    csv_filename = "osmos_augmented_clv_transactions.csv"
    print(f"Saving the full {len(transactions_aug):,} transactions to CSV: {csv_filename}")
    transactions_aug.to_csv(csv_filename, index=False)
else:
    transactions_excel = transactions_aug

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    customers_aug.to_excel(writer, sheet_name="Customers", index=False)
    transactions_excel.to_excel(writer, sheet_name="Transactions", index=False)
    clv_training.to_excel(writer, sheet_name="CLV_Training_Table", index=False)
    summary.to_excel(writer, sheet_name="Generation_Summary", index=False)

print(f"\nDone. File saved as: {OUTPUT_FILE}")