using Printf

function stress_test_infinite_scale_sum(x0::Float64=5.0, J::Int=3, num_stages::Int=10)
    println("=" ^ 70)
    println("PART 2: INFINITE SCALE RECURSION CONVERGENCE TEST (x0=$x0, J=$J)")
    println("=" ^ 70)

    # Set precision to 8000 bits (approx 2400 decimal digits) to prevent overflow
    setprecision(BigFloat, 8000)

    x_prev = BigFloat(x0)
    h_prev = x_prev ^ 1000  # D_0 = 1000 (Section 5.2)

    sum_delta_lambda = BigFloat(0.0)

    @printf("%-8s | %-12s | %-12s | %-12s | %-12s | %-15s | %-15s\n", 
            "Stage j", "x_{j-1}", "h_j", "k_j", "delta_j", "dH_j", "Cumul. Sum")
    println("-" ^ 95)

    for j in J:(J + num_stages - 1)
        j_bf = BigFloat(j)
        
        # Scale recursions (Eq 5.3)
        log_hj = x_prev / (j_bf^5)
        log_kj = x_prev / (j_bf^2)
        log_delta_j_inv = x_prev / (j_bf^3)
        
        hj = exp(log_hj)
        kj = exp(log_kj)
        delta_j = exp(-log_delta_j_inv)
        
        # Positive Pressure Hessian Increment (Section 5.7 / Eq 5.16)
        # Leading term cost: C * delta_j * h_j * h_{j-1} + k_j^{-1/4}
        leading_hessian_cost = delta_j * hj * h_prev
        remainder_cost = kj ^ -0.25
        dH_j = leading_hessian_cost + remainder_cost
        
        sum_delta_lambda += dH_j
        
        # Downcast to Float64 strictly for printing formatting
        @printf("%-8d | %-12.2e | %-12.4e | %-12.4e | %-12.4e | %-15.6e | %-15.6e\n", 
                j, Float64(x_prev), Float64(hj), Float64(kj), Float64(delta_j), Float64(dH_j), Float64(sum_delta_lambda))
        
        # Update for next stage
        x_prev = (j_bf^2) * x_prev
        h_prev = hj
    end

    println("-" ^ 95)
    @printf("Final Cumulative Pressure Hessian Sum : %.6e\n", Float64(sum_delta_lambda))
    println("Coercivity Preserved (Sum < 1.0)?    : ", sum_delta_lambda < 1.0)
    println("=" ^ 70, "\n")
end

# Run the stress test
stress_test_infinite_scale_sum(5.0, 3, 10)
