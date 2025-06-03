# Agent-Based International Trade Model Design
Date: January 6, 2025
Author: Claude & Kieran

## Mathematical Framework for Economic Agent Behavior

### Core Insight from Circular Flow Analysis

Your circular flow project revealed that:
1. National economic identities don't balance (14-26% imbalance)
2. Measurement methodologies matter more than raw data
3. Inter-component relationships are complex and non-linear
4. Time lags and frequencies create systemic discrepancies

These insights suggest agents should NOT assume equilibrium but rather operate under bounded rationality with imperfect information.

### Agent State Definition

Each nation-agent maintains state vector **N_i(t)**:

```
N_i(t) = {
    S_i(t): domestic savings rate
    T_i(t): tax revenue (% of GDP)
    M_i(t): import demand vector
    I_i(t): investment rate
    G_i(t): government spending
    X_i(t): export supply vector
    ε_i(t): measurement error/discrepancy
    P_i: production function parameters
    U_i: utility function parameters
    Ω_i(t): information set
}
```

### Production Function with Trade

Nation i's production incorporates domestic factors and imports:

```
Y_i(t) = A_i * K_i(t)^α * L_i(t)^β * Π_j[M_ij(t)^γ_ij]
```

Where:
- M_ij(t) = imports from country j
- γ_ij = elasticity of substitution
- Sum of exponents ≠ 1 (allowing for non-constant returns)

### Trade Decision Rules

#### Export Supply Function
```
X_ij(t) = f(p_ij(t), Y_i(t), capacity_i(t), policy_i(t))

Where:
- p_ij(t) = (e_j(t) * P_j(t)) / P_i(t) * (1 + τ_ij(t))
- e_j(t) = exchange rate
- τ_ij(t) = tariff rate
- policy_i(t) = export restrictions/subsidies
```

#### Import Demand Function
```
M_ij(t) = g(p_ji(t), Y_i(t), substitutes_i(t), policy_i(t))

Subject to:
- Balance of payments constraint
- Foreign exchange reserves
- Credit availability
```

### Information and Learning

Agents operate with imperfect, delayed information:

```
Ω_i(t) = {
    Own data: {S_i(t-1), T_i(t-1), ..., with noise}
    Partner data: {X_ji(t-k), M_ji(t-k), k ≥ 2}
    Global signals: {commodity prices, interest rates}
    Expectations: E[variable(t+h) | Ω_i(t)]
}
```

Learning mechanism:
```
E_i[X_j(t+1)] = E_i[X_j(t)] + α * (X_j(t-k) - E_i[X_j(t-k)])
```

### Policy Response Functions

#### Tariff Setting
```
τ_ij(t+1) = τ_base + β_1 * trade_deficit_i(t) + β_2 * unemployment_i(t) 
            + β_3 * political_pressure_i(t) + ε_policy
```

#### Monetary Policy
```
i_i(t+1) = taylor_rule(π_i(t), Y_gap_i(t)) + forex_pressure_i(t)
```

### Circular Flow Constraints (With Violations)

Each agent tries to satisfy:
```
S_i(t) + T_i(t) + M_i(t) ≈ I_i(t) + G_i(t) + X_i(t)
```

But allows for persistent imbalances:
```
ε_i(t) ~ N(μ_i, σ_i²)
```

Where μ_i and σ_i² are calibrated from your empirical findings (14-26% typical).

### Inter-Agent Interaction Protocol

1. **Negotiation Phase**:
   - Agents broadcast export availability
   - Bilateral negotiations based on:
     - Price competitiveness
     - Historical relationships
     - Policy constraints

2. **Execution Phase**:
   - Trade flows executed with delays
   - Payment settlements affect forex/reserves
   - Information updates with noise

3. **Adjustment Phase**:
   - Agents observe outcomes
   - Update expectations
   - Adjust policies

### Shock Propagation Mechanisms

Your circular flow analysis showed component interdependencies:

```
ΔS_i → ΔI_i (via interest rates)
ΔT_i → ΔG_i (fiscal constraint)
ΔM_i → ΔX_j (trade partner effect)
```

Shocks propagate through:
1. Trade linkages (import/export dependencies)
2. Financial channels (capital flows)
3. Expectation channels (confidence effects)

### Emergent Properties to Monitor

1. **Trade Network Formation**
   - Preferential partnerships emerge
   - Hub-and-spoke vs mesh topologies
   
2. **Contagion Patterns**
   - How local imbalances spread
   - Critical thresholds for cascades

3. **Policy Coordination**
   - Nash equilibria in tariff wars
   - Benefits of coordination vs defection

### Calibration from Your Data

Use your 50,000+ data points to:
1. Set realistic imbalance distributions
2. Calibrate adjustment speeds
3. Estimate policy reaction functions
4. Validate trade elasticities

### Implementation Architecture

```python
class NationAgent:
    def __init__(self, parameters, initial_state):
        self.state = initial_state
        self.params = parameters
        self.memory = CircularBuffer(1000)  # Limited memory
        self.partners = {}  # Trade relationships
        
    def perceive(self, global_state):
        # Noisy, delayed observations
        return add_noise(delay(global_state))
        
    def decide(self, observations):
        # Bounded rational decision making
        options = self.generate_options()
        return self.satisfice(options)  # Not optimize
        
    def act(self, decision):
        # Execute with friction/delays
        return self.execute_with_constraints(decision)
```

### Key Insights from Circular Flow Project

1. **Embrace Disequilibrium**: Agents should expect and plan for imbalances
2. **Measurement Matters**: Different agents may have different "truths"
3. **Time Inconsistency**: What balances annually may not monthly
4. **Structural Breaks**: Relationships change over time

This framework creates a more realistic simulation where:
- Perfect information doesn't exist
- Equilibrium is aspirational, not guaranteed
- Policy interventions have unintended consequences
- Small measurement differences compound into large effects

The result should be a teaching/research tool that demonstrates why simple trade models fail in practice and how real economies navigate persistent imbalances.