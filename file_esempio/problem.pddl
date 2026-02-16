;; problem.pddl
(define (problem salvataggio-aurelia)
  (:domain chiave-drago)

  (:objects
    eroe1 - eroe
    aurelia - principessa
    chiave-luce - artefatto
    drago1 - drago
    villaggio ingresso labirinto ponte tana-drago - luogo
  )

  (:init
    (at eroe1 villaggio)            ;; l’eroe parte dal villaggio
    (at aurelia tana-drago)         ;; la principessa è prigioniera nella tana
    (at chiave-luce tana-drago)     ;; la chiave è nella stessa tana
    (alive drago1)                  ;; il drago è vivo
    (skeleton-guarded labirinto)    ;; scheletri nel labirinto
    (bridge-intact)                 ;; il ponte è intatto
  )

  (:goal (and
    (rescued aurelia)               ;; la principessa deve essere salvata
    (sealed drago1)                 ;; il drago deve essere sigillato
  ))
)
