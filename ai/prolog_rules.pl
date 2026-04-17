% ==========================================================================================
% TESLA AUTONOMOUS DRIVING LOGIC - ULTRA-SAFE EDITION (v4.0)
% ==========================================================================================

% --- CONFIGURATION CONSTANTS (Global Params) ---
conf(emergency_limit, 65).
conf(pedestrian_limit, 120).
conf(safe_following, 160).
conf(side_merge_buffer, 90).
conf(max_speed, 105).
conf(comfort_speed, 85).

% ==========================================================================================
% MAIN DECISION RULE: select_action/8
% ==========================================================================================

select_action(Dist, LClear, RClear, Ped, LeadSpeed, MySpeed, Lane, Action) :-

    % -----------------------
    % 1. EMERGENCY & SURVIVAL LAYER
    % -----------------------
    % Case 1: Pedestrian emergency
    (Ped == true, Dist < 85 -> 
        Action = emergency_stop
    % Case 2: Rear-end collision imminent
    ; Dist < 60, MySpeed > LeadSpeed -> 
        Action = emergency_stop
    % Case 3: Sudden stop ahead
    ; LeadSpeed < 1.0, Dist < 70 -> 
        Action = emergency_stop
    % Case 4: Hard brake
    ; Dist < 50, LClear == false, RClear == false, MySpeed > 30 -> 
        Action = hard_brake

    % -----------------------
    % 2. ADVANCED TACTICAL MERGING
    % -----------------------
    % Case 5: Intelligent left pass
    ; Dist < 160, LeadSpeed < (MySpeed - 2), LClear == true, Lane > 0, Dist > 60 -> 
        Action = steer_left
    % Case 6: Intelligent right pass
    ; Dist < 160, LeadSpeed < (MySpeed - 2), RClear == true, Lane < 2, Dist > 60 -> 
        Action = steer_right
    % Case 7: Abort merge (high speed conflict)
    ; Dist < 60, MySpeed > 90 -> 
        Action = brake

    % -----------------------
    % 3. LANE DISCIPLINE & POSITIONING
    % -----------------------
    % Case 8: Yield fast lane
    ; Lane == 0, RClear == true, Dist > 200 -> 
        Action = steer_right
    % Case 9: Exit slow lane
    ; Lane == 2, LClear == true, Dist < 150 -> 
        Action = steer_left
    % Case 10: Lane centering
    ; Lane == 1, Dist > 140 -> 
        Action = maintain_speed

    % -----------------------
    % 4. ADAPTIVE CRUISE & SPEED CONTROL
    % -----------------------
    % Case 11: Speed matching
    ; Dist < 120, Dist > 70, MySpeed > LeadSpeed -> 
        Action = brake
    % Case 12: Predictive coasting
    ; Dist < 100, LeadSpeed > MySpeed -> 
        Action = coast
    % Case 13: Heavy traffic crawl
    ; Dist < 40, Dist > 15, MySpeed < 10 -> 
        Action = accelerate_gentle
    % Case 14: Speed limit cap
    ; MySpeed > 120 -> 
        Action = coast
    % Case 15: Open highway sprint
    ; Dist > 400 -> 
        Action = accelerate_hard
    % Case 16: Stable cruising
    ; Action = maintain_speed
    ).

% ==========================================================================================
% SAFETY VERIFICATION RULES
% ==========================================================================================

is_physical_gap_safe(FrontDist, SideClear, TargetLane) :-
    SideClear == true,
    FrontDist > 55,
    TargetLane >= 0,
    TargetLane =< 2.

check_risk(Dist, Ped, Status) :-
    (Ped == true -> Status = level_emergency
    ; Dist < 40 -> Status = level_critical
    ; Dist < 100 -> Status = level_caution
    ; Status = level_nominal).

is_boxed_in(L, R, D) :-
    L == false,
    R == false,
    D < 100.
