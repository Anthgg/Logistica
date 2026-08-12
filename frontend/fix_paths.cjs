const fs = require('fs');
const path = require('path');

const replacements = [
  {
    file: 'components/InventoryBalancePreparationPanel.tsx',
    from: '`/logistics/inventory-future-preparations/balance/${movementId}`',
    to: '`/logistics/inventory/movements/${movementId}/balance-preparation`'
  },
  {
    file: 'components/InventoryTraceabilityPreparationPanel.tsx',
    from: '`/logistics/inventory-future-preparations/traceability/${movementId}`',
    to: '`/logistics/inventory/movements/${movementId}/traceability-preparation`'
  },
  {
    file: 'pages/InventoryLedgerCheckpointsPage.tsx',
    from: "'/logistics/inventory-ledger-checkpoints'",
    to: "'/logistics/inventory/ledger/checkpoints'"
  },
  {
    file: 'pages/InventoryLedgerDashboardPage.tsx',
    from: "'/logistics/inventory-movements/dashboard'",
    to: "'/logistics/inventory/movements/dashboard'"
  },
  {
    file: 'pages/InventoryLedgerPartitionIntegrityPage.tsx',
    from: '`/logistics/inventory-ledger-partitions/${partitionId}/integrity`',
    to: '`/logistics/inventory/ledger/partitions/${partitionId}/integrity`'
  },
  {
    file: 'pages/InventoryLedgerPartitionsPage.tsx',
    from: "'/logistics/inventory-ledger-partitions'",
    to: "'/logistics/inventory/ledger/partitions'"
  },
  {
    file: 'pages/InventoryLedgerReconciliationPage.tsx',
    from: '`/logistics/inventory-ledger-reconciliation-jobs/${currentJob}`',
    to: '`/logistics/inventory/ledger/reconciliation-jobs/${currentJob}`'
  },
  {
    file: 'pages/InventoryLedgerReconciliationPage.tsx',
    from: '`/logistics/inventory-ledger-reconciliation-jobs/${currentJob}/results`',
    to: '`/logistics/inventory/ledger/reconciliation-jobs/${currentJob}/results`'
  }
];

const basePath = 'C:\\Users\\anthg\\OneDrive\\Escritorio\\proyecto tesis front\\frontend\\src\\features\\inventory-ledger';

for (const r of replacements) {
  const filePath = path.join(basePath, r.file);
  let content = fs.readFileSync(filePath, 'utf8');
  content = content.replace(r.from, r.to);
  fs.writeFileSync(filePath, content);
  console.log(`Updated ${r.file}`);
}
