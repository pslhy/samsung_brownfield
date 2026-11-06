# Dafny re-verification plan

## Changed symbols

- RingQueueModel.RingQueue.Clear                          body
- RingQueueModel.RingQueue.Offer                          body
- RingQueueModel.RingQueue.Poll                           body
- RingQueueModel.RingQueue.Snapshot                       body

## Must be re-verified: 4 of 49 symbols

- RingQueueModel.RingQueue.Clear                          <- body
- RingQueueModel.RingQueue.Offer                          <- body
- RingQueueModel.RingQueue.Poll                           <- body
- RingQueueModel.RingQueue.Snapshot                       <- body

## Java impact analysis vs. Dafny proof dependencies

Dafny symbols suggested by the Java impact set (changed + impacted, mapped): 18

In the Java impact set but NO re-verification needed (modular proofs): 14
- DispatcherModel.Dispatcher.DispatchOne
- DispatcherModel.Dispatcher.Drain
- DispatcherModel.Dispatcher.EvictOldestNonCritical
- DispatcherModel.Dispatcher.Submit
- PowerBudgetModel.PowerBudget.Headroom
- PowerBudgetModel.PowerBudget.IsIdle
- PowerBudgetModel.PowerBudget.IsRunning
- PowerBudgetModel.PowerBudget.Stop
- PowerBudgetModel.PowerBudget.StopAll
- PowerBudgetModel.PowerBudget.TotalLoad
- PowerBudgetModel.PowerBudget.TryStart
- RingQueueModel.RingQueue.IsEmpty
- RingQueueModel.RingQueue.Peek
- RingQueueModel.RingQueue.Size

Needs re-verification but NOT in the Java impact set (spec-only dependencies, e.g. a function used in contracts): 0

## Verification cost

full      :   1.5s wall | Dafny program verifier finished with 71 verified, 0 errors
selective :   1.0s wall | 1 dafny run(s), 9 extra symbol(s) verified by module runs

prover work (from the full run's log, start-up excluded):
  all symbols     :   1.35s solver time,      3800895 resource units
  selected only   :   0.14s solver time,       790432 resource units (21%)
